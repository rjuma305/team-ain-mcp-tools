"""
A simple MCP server implementation using FastAPI.

This server exposes two endpoints:

* **`/tools`** – returns a list of tool definitions loaded from `tools.json`.  ChatGPT uses this during the MCP handshake to discover available actions.
* **`/mcp`** – accepts JSON‑RPC 2.0 calls.  Each request must include a `method` (the tool name) and `params` (the tool parameters).  The server looks up the tool definition and dispatches to a corresponding Python function stub.  Responses follow the JSON‑RPC structure.

Tool functions are intentionally stubbed and should be implemented by you.  They currently log incoming parameters and return simple messages.  For write‑enabled tools, you should enforce your own policies (e.g. require approval or check `dry_run`) before performing any side effect.

To start the server locally:

```bash
pip install fastapi uvicorn pydantic
uvicorn mcp_server:app --reload
```

Then register `http://localhost:8000/mcp` as a connector endpoint in ChatGPT Developer Mode.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TOOLS_FILE = BASE_DIR / "tools.json"

app = FastAPI(title="MCP Starter Kit", version="0.1.0")


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    id: Optional[int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


def load_tools() -> Dict[str, Any]:
    """Load tool definitions from the tools.json file."""
    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            tools = json.load(f)
        # Build a lookup dict keyed by tool name for quick dispatch
        return {tool["name"]: tool for tool in tools}
    except Exception as exc:
        logger.error("Failed to load tools.json: %s", exc)
        return {}


TOOLS_LOOKUP = load_tools()


@app.get("/tools")
async def get_tools() -> Any:
    """Return the list of available tools."""
    return list(TOOLS_LOOKUP.values())


def _dispatch_tool(method: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
    """Dispatch the requested tool call.

    Each tool is implemented as a separate function prefixed with `tool_`.
    You can implement your tool logic here.
    """
    tool_def = TOOLS_LOOKUP.get(method)
    if not tool_def:
        raise ValueError(f"Unknown tool '{method}'")
    # Map tool names to Python functions
    func_name = method.replace(".", "_")  # e.g. slack.post -> slack_post
    handler = globals().get(f"tool_{func_name}")
    if not handler:
        raise NotImplementedError(f"No handler implemented for tool '{method}'")
    if params is None:
        params = {}
    return handler(**params)


@app.post("/mcp")
async def mcp_endpoint(req: JSONRPCRequest) -> Dict[str, Any]:
    """Handle a JSON‑RPC request."""
    if req.jsonrpc != "2.0":
        raise HTTPException(status_code=400, detail="Invalid JSON‑RPC version")
    try:
        result = _dispatch_tool(req.method, req.params)
        return {"jsonrpc": "2.0", "id": req.id, "result": result}
    except NotImplementedError as exc:
        logger.warning(str(exc))
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": str(exc)}}
    except Exception as exc:
        logger.exception("Error executing tool %s", req.method)
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32603, "message": str(exc)}}


# -----------------------------------------------------------------------------
# Tool handlers (stub implementations)
# -----------------------------------------------------------------------------


def tool_slack_post(channel: str, text: str, thread_ts: Optional[str] = None) -> Dict[str, Any]:
    """Post a message to Slack.

    Currently this is a stub.  Replace this with real Slack API calls.
    """
    logger.info("[slack.post] channel=%s text=%s thread_ts=%s", channel, text, thread_ts)
    # TODO: integrate with Slack API (e.g. via Slack WebClient)
    return {"status": "ok", "channel": channel, "message": text, "thread_ts": thread_ts}


def tool_mail_draft(to: str, subject: str, body_md: str) -> Dict[str, Any]:
    """Create an email draft.

    In a real implementation you would call the Gmail API here.
    """
    logger.info("[mail.draft] to=%s subject=%s", to, subject)
    # TODO: call Gmail connector or API to create a draft
    draft_id = "draft_12345"
    return {"draft_id": draft_id, "to": to, "subject": subject}


def tool_mail_send(draft_id: str, dry_run: bool = False) -> Dict[str, Any]:
    """Send a previously created draft.

    Use dry_run to preview the payload before actually sending.
    """
    logger.info("[mail.send] draft_id=%s dry_run=%s", draft_id, dry_run)
    if dry_run:
        return {"dry_run": True, "draft_id": draft_id}
    # TODO: call Gmail connector or API to send the draft
    return {"status": "sent", "draft_id": draft_id}


def tool_gha_run(owner: str, repo: str, workflow_id: str, ref: str, inputs: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """Trigger a GitHub Actions workflow.

    This function only logs the call.  Integrate with GitHub's REST API or CLI to dispatch workflows.
    """
    logger.info("[gha.run] owner=%s repo=%s workflow_id=%s ref=%s inputs=%s dry_run=%s", owner, repo, workflow_id, ref, inputs, dry_run)
    if dry_run:
        return {"dry_run": True, "workflow_id": workflow_id, "ref": ref, "inputs": inputs or {}}
    # TODO: integrate with GitHub API to dispatch the workflow
    return {"status": "queued", "workflow_id": workflow_id}


def tool_gha_status(run_id: str) -> Dict[str, Any]:
    """Get the status of a GitHub Actions run.

    This is a stub; implement real status lookups using the GitHub API.
    """
    logger.info("[gha.status] run_id=%s", run_id)
    # TODO: call GitHub API to retrieve run status
    return {"run_id": run_id, "status": "unknown"}


def tool_sql_query(name: str, text_sql: str, params: Optional[list[Any]] = None) -> Dict[str, Any]:
    """Execute a read‑only SQL query (stub).

    In production you would run the query against your database.  For demonstration,
    this simply logs the SQL and returns a fake result.
    """
    logger.info("[sql.query] name=%s sql=%s params=%s", name, text_sql, params)
    # TODO: execute against a real database
    return {"name": name, "rows": [], "columns": []}


def tool_chart_bar(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a bar chart from JSON data (stub).

    Replace this with calls to a charting library or service that returns image URLs.
    """
    logger.info("[chart.bar] data=%s", json_data)
    # TODO: integrate with chart generation (e.g. matplotlib + storage service)
    return {"url": "https://example.com/chart.png"}
