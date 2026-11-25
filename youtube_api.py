"""
Official YouTube Data API v3 Engine for APEX CINEGEN PRO
Direct API connection via OAuth2 (youtube_token.pickle)
Features:
- Live Channel Telemetry: Subscribers, Total Views, Video Count
- Top Performing Videos & Analytics
- Recent Viewer Comments & Community Engagement
- Resumable Chunked Video Uploading (MediaFileUpload)
"""

import os
import sys
import pickle
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import BASE_DIR, OUTPUT_DIR

TOKEN_FILE = BASE_DIR / "youtube_token.pickle"
SECRETS_FILE = BASE_DIR / "client_secrets.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_youtube_service():
    """Returns authenticated YouTube Data API service or None if not authenticated."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "wb") as f:
                    pickle.dump(creds, f)
        except Exception:
            creds = None

    if creds and creds.valid:
        try:
            return build("youtube", "v3", credentials=creds)
        except Exception:
            return None
    return None

def is_youtube_connected() -> bool:
    """Checks if youtube_token.pickle exists and is valid."""
    service = get_youtube_service()
    return service is not None

def get_channel_telemetry() -> Dict[str, Any]:
    """Retrieves live channel subscriber count, views, title, and video count."""
    service = get_youtube_service()
    if not service:
        return {
            "connected": False,
            "error": "OAuth token missing or expired. Run 'connect_youtube_channel.bat' to authenticate."
        }

    try:
        ch_res = service.channels().list(part="snippet,statistics", mine=True).execute()
        if "items" in ch_res and ch_res["items"]:
            item = ch_res["items"][0]
            snippet = item["snippet"]
            stats = item["statistics"]
            return {
                "connected": True,
                "title": snippet.get("title", "YouTube Channel"),
                "custom_url": snippet.get("customUrl", ""),
                "channel_id": item.get("id"),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url")
            }
        return {"connected": False, "error": "No channel found on this Google Account."}
    except Exception as e:
        return {"connected": False, "error": str(e)}

def get_top_videos(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns top performing videos on the authenticated channel."""
    service = get_youtube_service()
    if not service:
        return []

    try:
        # 1. Get uploads playlist
        ch_res = service.channels().list(part="contentDetails", mine=True).execute()
        if not ("items" in ch_res and ch_res["items"]):
            return []
        uploads_id = ch_res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # 2. Get playlist items
        pl_res = service.playlistItems().list(part="snippet", playlistId=uploads_id, maxResults=25).execute()
        vids = [it["snippet"]["resourceId"]["videoId"] for it in pl_res.get("items", [])]
        if not vids:
            return []

        # 3. Get video statistics
        vid_res = service.videos().list(part="snippet,statistics", id=",".join(vids)).execute()
        results = []
        for v in vid_res.get("items", []):
            st = v.get("statistics", {})
            sn = v.get("snippet", {})
            results.append({
                "id": v["id"],
                "title": sn.get("title", ""),
                "url": f"https://youtu.be/{v['id']}",
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0))
            })

        # Sort by view count
        results.sort(key=lambda x: x["views"], reverse=True)
        return results[:limit]
    except Exception:
        return []

def get_recent_comments(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches recent viewer comments on channel videos."""
    service = get_youtube_service()
    if not service:
        return []

    try:
        res = service.commentThreads().list(part="snippet", allThreadsRelatedToChannelId=get_channel_telemetry().get("channel_id"), maxResults=limit).execute()
        comments = []
        for item in res.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": top.get("authorDisplayName", "Viewer"),
                "text": top.get("textDisplay", ""),
                "published_at": top.get("publishedAt", "")
            })
        return comments
    except Exception:
        return []

from youtube_uploader import pack_youtube_tags_to_limit, VIRAL_SHERU_TAGS

def post_pinned_comment(service, video_id: str, comment_text: str) -> bool:
    """Posts an engagement discussion comment to boost YouTube algorithmic retention."""
    if not service or not comment_text:
        return False
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
        service.commentThreads().insert(part="snippet", body=body).execute()
        print(f"  [✓] Engagement comment posted on video {video_id}!")
        return True
    except Exception as e:
        print(f"  [!] Note on comment: {e}")
        return False

def upload_video_via_api(
    video_path: Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy_status: str = "private",
    publish_at: Optional[str] = None,
    thumbnail_path: Optional[Path] = None,
    pinned_comment: Optional[str] = None
) -> Dict[str, Any]:
    """Uploads video using official YouTube Data API v3 with resumable chunking and scheduled release support."""
    service = get_youtube_service()
    if not service:
        return {"success": False, "error": "OAuth token missing or expired."}

    video_path = Path(video_path)
    if not video_path.exists():
        return {"success": False, "error": f"Video not found: {video_path}"}

    # Format title with #Shorts
    clean_title = title.strip()
    if "#Shorts" not in clean_title and "#shorts" not in clean_title:
        if len(clean_title) + len(" #Shorts") <= 95:
            clean_title = f"{clean_title} #Shorts"
        else:
            clean_title = clean_title[:87] + "... #Shorts"
    clean_title = clean_title[:95]

    # Pack tags
    candidate_tags = (tags or []) + VIRAL_SHERU_TAGS
    packed_tags = pack_youtube_tags_to_limit(candidate_tags, max_limit=480)

    # Status setup
    status_dict = {
        "privacyStatus": "private" if publish_at else privacy_status.lower(),
        "selfDeclaredMadeForKids": False
    }
    if publish_at:
        status_dict["publishAt"] = publish_at

    body = {
        "snippet": {
            "title": clean_title,
            "description": description[:5000],
            "tags": packed_tags,
            "categoryId": "23",  # 23 = Comedy
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi"
        },
        "status": status_dict
    }

    print("\n" + "="*60)
    print("  [YouTube Data API v3] Uploading Video...")
    print("="*60)
    print(f"  🎬 Video     : {video_path.name}")
    print(f"  📌 Title     : {clean_title}")
    print(f"  🏷️ Packed Tags: {len(packed_tags)} tags ({sum(len(t) for t in packed_tags)} chars)")
    if publish_at:
        print(f"  📅 Scheduled : {publish_at} (UTC)")
    else:
        print(f"  👁️ Visibility: {privacy_status.upper()}")

    media = MediaFileUpload(str(video_path), chunksize=256*1024, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  [*] Upload progress: {int(status.progress() * 100)}%", end="\r")

    video_id = response.get("id")
    if not video_id:
        return {"success": False, "error": "No video ID returned by YouTube API."}

    print(f"\n  [✓] Video stream uploaded successfully: {video_id}")

    # Upload thumbnail if available
    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            service.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path))).execute()
            print(f"  [✓] Custom thumbnail uploaded: {Path(thumbnail_path).name}")
        except Exception as e:
            print(f"  [!] Note on thumbnail upload: {e}")

    # Post pinned comment if provided
    if pinned_comment:
        post_pinned_comment(service, video_id, pinned_comment)

    yt_link = f"https://www.youtube.com/shorts/{video_id}"
    print("="*60)
    print("  🎉 YOUTUBE PUBLISHING COMPLETE!")
    print(f"  👉 Watch / Share: {yt_link}")
    print("="*60 + "\n")

    return {
        "success": True,
        "video_id": video_id,
        "link": yt_link,
        "title": clean_title,
        "status": "scheduled" if publish_at else privacy_status,
        "publish_at": publish_at
    }

if __name__ == "__main__":
    status = get_channel_telemetry()
    print("Channel Status:", status)
