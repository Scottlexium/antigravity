use zed_extension_api::{self as zed, Result};

struct AntigravityExtension {
    // State goes here. For example, we might track if the daemon is running.
}

impl zed::Extension for AntigravityExtension {
    fn new() -> Self {
        AntigravityExtension {}
    }

    /// This function is called by Zed when it needs to start a server for this extension.
    /// We can use this to spawn our Antigravity Bridge Daemon.
    fn language_server_command(
        &mut self,
        _language_server_id: &zed::LanguageServerId,
        _worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        
        // This bash script automatically provisions the Python environment on the user's machine
        // inside a hidden folder in their home directory, making the extension portable and publishable!
        let bootstrap_script = "
# Ensure our hidden state directory exists
mkdir -p \"$HOME/.zed_antigravity\"
cd \"$HOME/.zed_antigravity\"

# If the virtual environment doesn't exist, create it and install dependencies
if [ ! -d \"venv\" ]; then
    echo \"Initializing Python environment for Antigravity...\" >&2
    python3 -m venv venv
    venv/bin/pip install fastapi uvicorn google-antigravity python-dotenv
    
    # Download the latest daemon script straight from your GitHub repository!
    curl -sL https://raw.githubusercontent.com/Scottlexium/antigravity/master/daemon/server.py -o server.py
fi

# Execute the local proxy daemon natively
exec venv/bin/python server.py
".to_string();
        
        Ok(zed::Command {
            command: "/bin/bash".to_string(),
            args: vec!["-c".to_string(), bootstrap_script],
            env: vec![],
        })
    }
}

zed::register_extension!(AntigravityExtension);
