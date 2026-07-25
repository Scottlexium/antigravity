# Zed Antigravity Extension

## The Problem
Google stopped Gemini support for third-party editors like Zed. Users who want to use Gemini for AI-assisted coding in Zed are left without a native option.

## The Idea
We will build a Zed extension that leverages the **Antigravity CLI & SDK** to restore Gemini capabilities in Zed. 

Zed handles AI in a few ways:
1. **AI Providers (Chat/Inline):** Native support for OpenAI-compatible endpoints.
2. **MCP (Model Context Protocol):** Allows extensions to provide context/tools to the AI.
3. **Language Servers (LSP):** Standard way to provide autocomplete and diagnostics.

Since Zed extensions can manage the lifecycle of background binaries, our extension will act as a **manager for a local Antigravity Bridge Daemon**.

### Architecture
1. **The Rust/Wasm Extension (`src/lib.rs`):**
   - Runs inside Zed.
   - Automatically downloads/starts a lightweight local background server (the "Bridge Daemon").
   - Monitors the daemon's health.
   
2. **The Antigravity Bridge Daemon:**
   - A local HTTP server that exposes an **OpenAI-compatible API** (`/v1/chat/completions`).
   - Zed will be configured to send its Assistant Panel requests to this daemon.
   - The daemon intercepts these requests and translates them into **Antigravity SDK / Gemini API** calls.
   
3. **MCP Integration (Bonus Phase):**
   - The extension will also register the daemon as an **MCP Server**.
   - This allows Zed's AI to use Antigravity's powerful agentic tools (like `agy` tools, codebase scanning, and terminal execution) directly from the Zed chat interface via slash commands.

## Setup Steps (Future Implementation)
1. Write the Rust Wasm extension to spawn a local command.
2. Write the Bridge Daemon (in Rust or Node/Python) that wraps the Antigravity SDK.
3. Configure Zed's `settings.json` to point the custom OpenAI provider to the daemon's port.


