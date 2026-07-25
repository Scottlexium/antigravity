import json
import uvicorn
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.models import GeminiAPIEndpoint, VertexEndpoint, ModelTarget

from contextlib import asynccontextmanager

# Cache the agent instance so we don't spawn it on every request
global_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global global_agent
    if global_agent is not None:
        await global_agent.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

async def get_or_create_agent(auth_header: str):
    global global_agent
    
    if global_agent is not None:
        return global_agent
        
    # Extract API key from Zed's header if present
    api_key = None
    if auth_header and auth_header.startswith("Bearer "):
        extracted_key = auth_header.replace("Bearer ", "").strip()
        if len(extracted_key) > 10 and "dummy" not in extracted_key.lower():
            api_key = extracted_key

    # Fallback to environment variables
    env_api_key = os.environ.get("GEMINI_API_KEY")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    gcp_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    # 🚨 CRITICAL FIX: The Antigravity SDK often overrides models and looks directly at the env vars.
    # We will inject the API key straight into the environment so the SDK finds it.
    actual_key = api_key or env_api_key
    if actual_key:
        print("Using Gemini API Key authentication...")
        os.environ["GEMINI_API_KEY"] = actual_key
        config = LocalAgentConfig(
            system_instructions="You are Antigravity running inside the Zed editor. You have full access to the user's workspace and terminal. Prioritize writing code and editing files to help the user.",
            capabilities=CapabilitiesConfig(),
            api_key=actual_key  # Pass it directly here too!
        )
    elif gcp_project:
        print("Using Google Cloud Application Default Credentials (OAuth)...")
        endpoint = VertexEndpoint(project=gcp_project, location=gcp_location)
        config = LocalAgentConfig(
            system_instructions="You are Antigravity running inside the Zed editor. You have full access to the user's workspace and terminal. Prioritize writing code and editing files to help the user.",
            capabilities=CapabilitiesConfig(),
            models=[ModelTarget(name="default", endpoint=endpoint)]
        )
    else:
        raise ValueError(
            "No authentication found! Please provide a Gemini API key in Zed's UI, "
            "set GEMINI_API_KEY in your terminal, or set GOOGLE_CLOUD_PROJECT to use browser OAuth."
        )
    
    print("Spawning Antigravity Agent backend with detected auth...")
    agent = Agent(config)
    await agent.__aenter__()
    global_agent = agent
    print("Agent spawned successfully! Ready to process requests.")
    return global_agent


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = await request.json()
    messages = payload.get("messages", [])
    
    if not messages:
        return {}

    prompt_data = messages[-1].get("content", "")
    prompt = ""
    if isinstance(prompt_data, str):
        prompt = prompt_data
    elif isinstance(prompt_data, list):
        # Handle OpenAI multimodal format (list of dicts)
        prompt = "".join([item.get("text", "") for item in prompt_data if isinstance(item, dict) and item.get("type") == "text"])
    elif isinstance(prompt_data, dict):
        prompt = prompt_data.get("text", "")
    
    print(f"[Zed] Received Prompt: {prompt}")
    
    auth_header = request.headers.get("Authorization", "")
    try:
        agent = await get_or_create_agent(auth_header)
    except Exception as e:
        print(f"Auth Error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))

    async def stream_antigravity():
        response = await agent.chat(prompt)
        async for token in response:
            chunk = {
                "id": "chatcmpl-antigravity",
                "object": "chat.completion.chunk",
                "model": "antigravity-bridge",
                "choices": [{
                    "index": 0,
                    "delta": {"content": token},
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        
        finish_chunk = {
            "id": "chatcmpl-antigravity",
            "object": "chat.completion.chunk",
            "model": "antigravity-bridge",
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(finish_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(stream_antigravity(), media_type="text/event-stream")

if __name__ == "__main__":
    import sys
    import logging
    
    # CRITICAL: Since Zed spawns this as a Language Server, it expects JSON-RPC over stdout.
    # We must suppress Uvicorn's stdout logs so we don't break Zed's IPC channel.
    logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
    logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)

    print("Starting Antigravity Bridge Daemon on http://127.0.0.1:8080...", file=sys.stderr)
    
    # Start the server with no log config to prevent stdout spam
    uvicorn.run(app, host="127.0.0.1", port=8080, log_config=None)

