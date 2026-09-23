"""Setup script to run the Google Drive OAuth flow and save drive_token.json.

This script:
1. Reads OAuth client credentials from:
   - Existing ``token.json`` (Desktop Client ID)
   - ``mcp_config.json`` (Drive MCP credentials)
   - ``client_secret.json`` / ``drive_client_secret.json``
2. Runs the OAuth authorization flow in your browser.
3. Saves the resulting credentials to ``backend/drive_token.json``.
"""

import json
import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def get_available_credentials() -> list[dict]:
    """Find all potential OAuth client credentials available in the project."""
    script_dir = Path(__file__).resolve().parent
    creds_list = []

    # 1. Check existing token.json (Desktop client used by Gmail)
    token_path = script_dir / "token.json"
    if token_path.is_file():
        try:
            tdata = json.loads(token_path.read_text(encoding="utf-8"))
            cid = tdata.get("client_id")
            csec = tdata.get("client_secret")
            if cid and csec:
                creds_list.append({
                    "name": "Desktop Client (from token.json - Recommended for local sign-in)",
                    "config": {
                        "installed": {
                            "client_id": cid,
                            "client_secret": csec,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
                        }
                    },
                })
        except Exception:
            pass

    # 2. Check mcp_config.json
    mcp_config_path = Path(os.path.expanduser("~")) / ".gemini" / "config" / "mcp_config.json"
    if mcp_config_path.is_file():
        try:
            mcp_data = json.loads(mcp_config_path.read_text(encoding="utf-8"))
            drive_oauth = mcp_data.get("mcpServers", {}).get("drive", {}).get("oauth", {})
            cid = drive_oauth.get("clientId")
            csec = drive_oauth.get("clientSecret")
            if cid and csec:
                creds_list.append({
                    "name": f"Drive MCP Client (from mcp_config.json - {cid[:18]}...)",
                    "config": {
                        "installed": {
                            "client_id": cid,
                            "client_secret": csec,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost", "http://localhost:8080", "urn:ietf:wg:oauth:2.0:oob"],
                        }
                    },
                })
        except Exception:
            pass

    # 3. Check client_secret.json / drive_client_secret.json
    for name in ["drive_client_secret.json", "client_secret.json"]:
        p = script_dir / name
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if "installed" in data or "web" in data:
                    creds_list.append({
                        "name": f"JSON File ({name})",
                        "config": data,
                    })
            except Exception:
                pass

    return creds_list


def main():
    print("=" * 65)
    print(" Google Drive OAuth Setup for Jarvis")
    print("=" * 65)

    creds_options = get_available_credentials()
    if not creds_options:
        print("\n❌ No OAuth client credentials found.")
        print("Please place a Google OAuth Desktop client credentials file at backend/client_secret.json")
        return

    print("\nSelect OAuth Client to use:")
    for i, opt in enumerate(creds_options, 1):
        print(f" [{i}] {opt['name']}")

    choice = 1
    if len(creds_options) > 1:
        user_input = input(f"\nEnter choice [1-{len(creds_options)}] (default 1): ").strip()
        if user_input.isdigit() and 1 <= int(user_input) <= len(creds_options):
            choice = int(user_input)

    selected = creds_options[choice - 1]
    print(f"\nUsing: {selected['name']}")

    script_dir = Path(__file__).resolve().parent
    client_config = selected["config"]

    # Set fixed redirect URIs for port 8080
    fixed_redirect_uris = [
        "http://localhost:8080/",
        "http://localhost:8080",
        "http://127.0.0.1:8080/",
        "http://localhost",
        "urn:ietf:wg:oauth:2.0:oob"
    ]
    if "installed" in client_config:
        client_config["installed"]["redirect_uris"] = fixed_redirect_uris
    elif "web" in client_config:
        client_config["web"]["redirect_uris"] = fixed_redirect_uris

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\nStarting local authorization flow on http://localhost:8080/ ...")
    print("Add this redirect URI to Google Cloud Console if needed:")
    print("  👉 http://localhost:8080/")

    try:
        creds = flow.run_local_server(port=8080, open_browser=True)
    except Exception as e:
        print(f"\n❌ OAuth flow failed on port 8080: {e}")
        return

    token_path = script_dir / "drive_token.json"
    token_path.write_text(creds.to_json(), encoding="utf-8")

    print(f"\n✅ Google Drive credentials successfully saved to:\n   {token_path}")
    print("\nJarvis can now access your Google Drive files!")


if __name__ == "__main__":
    main()
