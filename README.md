# MCP Starter Kit

This directory contains a minimal skeleton for building custom MCP (Model Context Protocol) servers and prompts for OpenAI’s ChatGPT Developer Mode.  It includes:

* **`mcp_server.py`** – a basic FastAPI application exposing an `/mcp` endpoint that accepts JSON‑RPC requests and returns responses.  It also exposes a `/tools` endpoint that returns the available tool specifications used during the MCP handshake.
* **`tools.json`** – a JSON file describing the available tools.  Each tool entry includes the tool name, description, parameters schema, whether it is read‑only, and policy annotations (such as `requires_approval`).  These definitions mirror the examples provided in the implementation plan.
* **`policy.json`** – a starting point for an MCP Guard policy.  The allowlist, denylist, approval routing and other safety controls live here.  In production you should extend this with your own environment‑specific rules.
* **`prompts/`** – a set of system prompt templates for different agent personas (Support Concierge, CloudOps Engineer, Content Studio, Analytics Co‑Pilot).  These prompts can be used when creating a Developer Mode conversation to guide ChatGPT’s behaviour.
* **`notion_kb/`** – an example knowledge base structure organised into FAQs, standard operating procedures (SOPs) and playbooks.  Populate these markdown files with your organisation’s content and link them to your Notion or other knowledge store.

To run the server locally you will need Python 3.9+ and FastAPI installed.  You can install dependencies and start the server with:

```
pip install fastapi uvicorn pydantic
uvicorn mcp_server:app --reload
```

The server currently stubs out tool functions – they simply log the incoming parameters.  To make it useful you will need to implement the logic for each tool (e.g. sending email drafts via Gmail, posting messages to Slack, or dispatching GitHub Actions).  See the `TODO` comments in `mcp_server.py` for guidance.

The intention is that you register the running server’s `/mcp` URL as a connector in ChatGPT’s Developer Mode.  ChatGPT will perform the MCP handshake against `/mcp` and then you can instruct it to call your tools.

> **Important:** This starter kit does not implement authentication or authorisation.  When exposing your MCP server publicly you should require OAuth or other mechanisms to protect your services.  See OpenAI’s documentation and your organisation’s security policies for recommendations.
