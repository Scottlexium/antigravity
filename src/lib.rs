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
        
        // In a production extension, this would download a bundled binary.
        // For this custom setup, we use the absolute paths to the python environment.
        let python_path = "/Users/scottlexium/projects/zed-antigravity-extension/daemon/venv/bin/python".to_string();
        let script_path = "/Users/scottlexium/projects/zed-antigravity-extension/daemon/server.py".to_string();
        
        Ok(zed::Command {
            command: python_path,
            args: vec![script_path],
            env: vec![],
        })
    }
}

zed::register_extension!(AntigravityExtension);
