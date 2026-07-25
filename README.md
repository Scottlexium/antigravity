# Antigravity

Antigravity brings Gemini AI into the Zed editor. It runs a lightweight background service on your machine that Zed talks to via its built-in custom AI provider support.

---

## How it works

A small Python server runs silently in the background on `localhost:8080`. It exposes an OpenAI-compatible API that Zed natively understands. Every chat message you send in Zed's Assistant Panel goes to this server, which forwards it to Google's Gemini via the Antigravity SDK and streams the response back.

The server is managed by macOS's built-in `launchd` service manager, so it starts automatically when you log in and restarts itself if it ever crashes.

---

## Installation

Run this in your terminal:

```bash
curl -sL https://raw.githubusercontent.com/Scottlexium/antigravity/master/install.sh | bash
```

That's it. The script will:
- Create a Python environment in `~/.zed_antigravity`
- Install all dependencies
- Register the background service so it starts at login

---

## Zed Setup

After running the installer, configure Zed once:

1. Open **Zed Settings** → **AI**
2. Click **Add Provider** → choose **OpenAI Compatible**
3. Fill in:
   - **URL:** `http://127.0.0.1:8080/v1`
   - **API Key:** Your Gemini API key ([get one here](https://aistudio.google.com/app/apikey))
   - **Model:** `antigravity-bridge`

Open the Assistant Panel (`Cmd+Shift+A`) and start chatting.

---

## Authentication options

| Method | How |
|--------|-----|
| Gemini API Key (Zed UI) | Paste your key into Zed's API Key field |
| Gemini API Key (terminal) | `export GEMINI_API_KEY=your-key` before starting the service |
| Google Cloud OAuth | `gcloud auth application-default login` + `export GOOGLE_CLOUD_PROJECT=your-project` |

---

## Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.scottlexium.antigravity.plist
rm ~/Library/LaunchAgents/com.scottlexium.antigravity.plist
rm -rf ~/.zed_antigravity
```

---

## Project layout

```
antigravity/
├── install.sh                          # One-shot setup script for users
├── daemon/
│   ├── server.py                       # The FastAPI proxy server
│   ├── requirements.txt                # Python dependencies
│   └── com.scottlexium.antigravity.plist   # macOS launchd service definition
├── src/lib.rs                          # Zed extension Rust/Wasm core
├── extension.toml                      # Extension manifest
└── Cargo.toml
```
