"""
YouTube OAuth Token Generator & Refresher
Generates a persistent youtube_token.pickle for official YouTube Data API v3 access.
Provides live channel stats, comments, top performing videos, and API uploads.
"""

import sys
import pickle
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from banner import print_creator_terminal_banner

BASE_DIR = Path(__file__).resolve().parent
SECRETS_FILE = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "youtube_token.pickle"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def authenticate_youtube():
    print_creator_terminal_banner(project_name="APEX CINEGEN — YOUTUBE OAUTH CONNECT")
    print("=" * 65)
    print("  🔑 YOUTUBE DATA API V3 — OAUTH AUTHENTICATION")
    print("=" * 65)

    if not SECRETS_FILE.exists():
        print(f"❌ Error: {SECRETS_FILE.name} not found in project directory.")
        return False

    print("\n🌐 Opening browser for Google Account authentication...")
    print("👉 Please select your YouTube channel's Google Account and click Allow.")
    
    flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    print("\n💾 Saving credentials to youtube_token.pickle...")
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    print("✅ Local token saved successfully!")

    print("\n🔍 Verifying YouTube Data API access...")
    try:
        youtube = build("youtube", "v3", credentials=creds)
        ch = youtube.channels().list(part="snippet,statistics", mine=True).execute()
        if "items" in ch and ch["items"]:
            item = ch["items"][0]
            title = item["snippet"]["title"]
            cid = item["id"]
            subs = item["statistics"].get("subscriberCount", "N/A")
            views = item["statistics"].get("viewCount", "N/A")
            vids = item["statistics"].get("videoCount", "N/A")
            
            print("\n" + "=" * 65)
            print("  🎉 YOUTUBE CHANNEL CONNECTED SUCCESSFULLY!")
            print("=" * 65)
            print(f"  📺 Channel Name : {title}")
            print(f"  🆔 Channel ID   : {cid}")
            print(f"  👥 Subscribers  : {subs}")
            print(f"  👁️ Total Views  : {views}")
            print(f"  🎬 Total Videos : {vids}")
            print("=" * 65)
            print("\n✅ Your Telegram Bot and automation now have direct LIVE channel stats!")
            return True
        else:
            print("⚠️ Authenticated, but no YouTube channel found on this Google account.")
            return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    authenticate_youtube()
