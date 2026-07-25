# Antigravity

Gemini in Zed. No subscriptions, no lock-in — just your own API key and the full power of Google's Gemini models running natively inside the editor.

Google removed Gemini support from third-party editors, so this extension brings it back. It runs a small background service on your machine that Zed talks to through its built-in custom AI provider support. From there, everything works exactly like any other AI provider in Zed — inline edits, the assistant panel, the works.

---

## Getting started

### Step 1 — Get a Gemini API key

You need a free Gemini API key from Google AI Studio.

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key — it'll look something like `AIzaSy...`

That's your key. Keep it somewhere safe.

### Step 2 — Install the background service

Open a terminal and run:

```bash
git clone https://github.com/Scottlexium/antigravity
cd antigravity && bash install.sh
```

This will set up a small background service on your Mac (`~/.zed_antigravity`) that starts automatically at login and restarts itself if it ever goes down. You only need to do this once.

### Step 3 — Connect Zed

1. Open Zed and go to **Settings → AI**
2. Click **Add Provider** and choose **OpenAI Compatible**
3. Fill in the following:
   - **URL:** `http://127.0.0.1:8080/v1`
   - **API Key:** the Gemini key you copied in Step 1
   - **Model:** `antigravity-bridge`
4. Open the Assistant Panel (`Cmd+Shift+A`) and start chatting

---

## Authentication options

You have three ways to authenticate. Pick whichever works best for you:

| Method | How to use |
|--------|------------|
| **Gemini API Key (recommended)** | Paste your key into Zed's API Key field as described above |
| **Environment variable** | `export GEMINI_API_KEY=your-key` before the service starts |
| **Google Cloud OAuth** | Run `gcloud auth application-default login` once, then `export GOOGLE_CLOUD_PROJECT=your-project-id` |

---

## Uninstalling

```bash
launchctl bootout "gui/$(id -u)" ~/Library/LaunchAgents/com.scottlexium.antigravity.plist
rm ~/Library/LaunchAgents/com.scottlexium.antigravity.plist
rm -rf ~/.zed_antigravity
```

---

## Requirements

- macOS (the background service uses launchd)
- Python 3 (comes with macOS)
- A Gemini API key — free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## How it works

The installer sets up a lightweight Python server at `localhost:8080`. It exposes an OpenAI-compatible API that Zed already understands. When you chat in the Zed assistant panel, your message goes to this local server, which passes it to Gemini via the official `google-antigravity` SDK, and streams the response back into Zed in real time.

The background service is managed by macOS's built-in launchd, so it starts on login and stays running without any terminal windows open.

---

## License

MIT
