import json
import uvicorn
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.models import VertexEndpoint, ModelTarget
from contextlib import asynccontextmanager

# We create a fresh agent per request so it can be given the correct
# working directory (i.e. the user's actual open project in Zed).
# A cached agent keyed by workspace path avoids redundant re-spawning.
_agent_cache: dict[str, Agent] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up all cached agents on shutdown
    for agent in _agent_cache.values():
        await agent.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)


def _build_config(api_key: str | None, gcp_project: str | None, workspace: str) -> LocalAgentConfig:
    """Build a LocalAgentConfig for the given workspace and auth details."""

    system_prompt = (
        "You are a helpful AI assistant running inside the Zed editor. "
        "Answer the user's questions directly and concisely. "
        "When the user asks you to write, edit, or explain code, do so. "
        f"The user's current workspace is: {workspace}. "
        "Only explore the filesystem or run commands when the user explicitly asks you to."
    )

    if gcp_project:
        endpoint = VertexEndpoint(
            project=gcp_project,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        return LocalAgentConfig(
            system_instructions=system_prompt,
            capabilities=CapabilitiesConfig(),
            models=[ModelTarget(name="default", endpoint=endpoint)]
        )

    return LocalAgentConfig(
        system_instructions=system_prompt,
        capabilities=CapabilitiesConfig(),
        api_key=api_key
    )


async def get_agent(auth_header: str, workspace: str) -> Agent:
    """Return a cached agent for this workspace, or spawn a new one."""
    global _agent_cache

    if workspace in _agent_cache:
        return _agent_cache[workspace]

    # Resolve API key — prefer Zed's Authorization header, fall back to env var
    api_key: str | None = None
    if auth_header and auth_header.startswith("Bearer "):
        candidate = auth_header.removeprefix("Bearer ").strip()
        if len(candidate) > 10 and "dummy" not in candidate.lower():
            api_key = candidate

    env_key = os.environ.get("GEMINI_API_KEY")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    actual_key = api_key or env_key

    if not actual_key and not gcp_project:
        raise ValueError(
            "No authentication found. Add your Gemini API key in Zed's AI provider settings, "
            "set GEMINI_API_KEY in your environment, or configure GOOGLE_CLOUD_PROJECT for OAuth."
        )

    # Inject into env so the SDK's internal validator is satisfied
    if actual_key:
        os.environ["GEMINI_API_KEY"] = actual_key

    config = _build_config(actual_key, gcp_project, workspace)

    print(f"Spawning agent for workspace: {workspace}", flush=True)
    agent = Agent(config)
    await agent.__aenter__()
    _agent_cache[workspace] = agent
    print("Agent ready.", flush=True)
    return agent


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()
    messages = payload.get("messages", [])

    if not messages:
        return {}

    # Extract the plain-text prompt from whatever shape Zed sends
    raw = messages[-1].get("content", "")
    if isinstance(raw, str):
        prompt = raw
    elif isinstance(raw, list):
        prompt = "".join(
            item.get("text", "") for item in raw
            if isinstance(item, dict) and item.get("type") == "text"
        )
    elif isinstance(raw, dict):
        prompt = raw.get("text", "")
    else:
        prompt = str(raw)

    # Zed sends the open project path in a custom header — use it so the
    # agent knows which workspace it's operating in.
    workspace = (
        request.headers.get("X-Zed-Workspace")
        or request.headers.get("X-Workspace")
        or os.path.expanduser("~")
    )

    auth_header = request.headers.get("Authorization", "")
    try:
        agent = await get_agent(auth_header, workspace)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    async def stream():
        response = await agent.chat(prompt)
        async for token in response:
            yield f"data: {json.dumps({'id': 'chatcmpl-ag', 'object': 'chat.completion.chunk', 'model': 'antigravity-bridge', 'choices': [{'index': 0, 'delta': {'content': token}, 'finish_reason': None}]})}\n\n"

        yield f"data: {json.dumps({'id': 'chatcmpl-ag', 'object': 'chat.completion.chunk', 'model': 'antigravity-bridge', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import sys
    import logging
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
    print("Antigravity Bridge Daemon running on http://127.0.0.1:8080", file=sys.stderr)
    uvicorn.run(app, host="127.0.0.1", port=8080, log_config=None)
