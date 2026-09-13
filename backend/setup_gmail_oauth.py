"""Setup script to run the Google Gmail OAuth flow and save token.json.

This script:
1. Uses the client_secret.json (Google OAuth Desktop app credentials)
2. Opens a browser window for you to grant permission
3. Saves the resulting credentials to ``backend/token.json``
4. The Gmail tools (SendEmailTool, ListRecentEmailsSkill) automatically
   pick up ``token.json`` from the module directory or the project root.

Before running, make sure you have:
* A Google Cloud project with the Gmail API enabled
* An OAuth 2.0 Desktop Client ID created (client_secret.json)
* Installed: ``pip install google-auth-oauthlib google-auth ``
"""
import time
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


def main():
    # ------------------------------------------------------------------
    # 1. Locate client_secret.json
    # ------------------------------------------------------------------
    # Preferred: next to this script
    script_dir = Path(__file__).resolve().parent
    client_path = script_dir / "client_secret.json"

    # Fallback: project root
    if not client_path.is_file():
        client_path = Path(__file__).resolve().parents[4] / "client_secret.json"

    if not client_path.is_file():
        raise FileNotFoundError(
            f"client_secret.json not found at {client_path}. "
            "Place your Google OAuth Desktop Client JSON there."
        )

    # ------------------------------------------------------------------
    # 2. Choose scope: send vs read-only
    # ------------------------------------------------------------------
    # "gmail.send"     => can send email on behalf of the user
    # "gmail.readonly" => can list/search emails (needed by list_recent_emails)
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    # ------------------------------------------------------------------
    # 3. Run the local-OAuth flow
    # ------------------------------------------------------------------
    print(f"Starting OAuth flow using {client_path} …")
    print("A browser window will open. Follow the steps, then close the window.")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=0)

    # ------------------------------------------------------------------
    # 4. Save token.json
    # ------------------------------------------------------------------
    # The Gmail tools look for token.json at backend/ (project root) or next
    # to the module — save it where the tools actually read it from.
    token_path = script_dir / "token.json"
    token_path.write_text(creds.to_json())

    print(f"\n✅ Credentials saved to {token_path}")
    print("You can now run the Gmail tool tests:")
    print("  python -m pytest tests\\unit\\test_gmail_tools.py tests\\unit\\test_gmail_pipelines.py -v")
    input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()