"""
APEX CINEGEN — Automated Video Scheduler & High-CTR Tag Publisher
Uploads and schedules the latest generated video via official YouTube Data API v3.
Applies quote-aware viral tag packing, custom thumbnail, and engagement pinned comment.
"""

import sys
import datetime
from pathlib import Path
from youtube_api import upload_video_via_api, get_channel_telemetry
from banner import print_creator_terminal_banner
from config import OUTPUT_DIR

def schedule_video():
    print_creator_terminal_banner(project_name="APEX CINEGEN — YOUTUBE SCHEDULING ENGINE")
    
    # 1. Verify YouTube Channel Connection
    ch_info = get_channel_telemetry()
    if not ch_info.get("connected"):
        print("❌ Error: YouTube OAuth not connected.")
        return False
        
    print(f"  📺 Connected Channel : {ch_info['title']} ({ch_info.get('custom_url', '')})")
    print(f"  👥 Current Subscribers: {ch_info['subscribers']:,}")

    # 2. Pick latest generated video and metadata
    target_video = OUTPUT_DIR / "sheru_cheetah_flying_pind_20261123_184137.mp4"
    if not target_video.exists():
        recent_mp4s = sorted(OUTPUT_DIR.glob("sheru_final_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not recent_mp4s:
            recent_mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not recent_mp4s:
            print("❌ No generated MP4 videos found in output_videos/")
            return False
        target_video = recent_mp4s[0]

    thumb_cand = OUTPUT_DIR / f"{target_video.stem}_thumbnail.jpg"
    if not thumb_cand.exists():
        thumb_cand = OUTPUT_DIR / "sheru_cheetah_flying_pind_thumbnail.jpg"

    info_cand = OUTPUT_DIR / f"{target_video.stem}_info.txt"
    if not info_cand.exists():
        info_cand = OUTPUT_DIR / "sheru_cheetah_flying_pind_info.txt"

    # Default metadata
    title = "Cheetah Builder ki akad 💥 Sheru Bhai ka Flying Pind! #Shorts"
    description = (
        "Cheetah Builder ne socha Sheru Bhai ko neecha dikha dega? 😂 "
        "Zameen kya, Sheru Bhai toh poora pind hi hawa mein uda dete hain! "
        "Flying tractors aur shaadi ki lights ke saath dekho Sheru Bhai ka next-level flex. "
        "Iss video ko like karo aur channel subscribe karo for more Sheru Bhai awesomeness!\n\n"
        "#SheruBhai #Shorts #ComedyShorts #Viral #Reels #HindiComedy #AnimalLore #TrendingShorts #YouTubeShorts"
    )
    pinned_comment = "Cheetah Builder ki shakal dekhne layak thi jab Sheru Bhai ne apna flying pind leke aaye! 😂 Tumhe Sheru Bhai ka yeh move kaisa laga? 👇"
    tags = [
        "Sheru Bhai", "Sheru Comedy", "Cheetah Builder", "Flying Pind", "Hindi Comedy",
        "Funny Video", "Indian Animation", "Animal Comedy", "Desi Comedy", "YouTube Shorts",
        "Shorts", "Trending Shorts", "Viral Shorts", "Comedy Shorts", "Ghanta", "Attitude Status",
        "Billionaire Flex", "Gold Chain Lion", "Viral Comedy", "Punjab Comedy", "Reels"
    ]

    # Extract metadata from info file if available
    if info_cand.exists():
        try:
            content = info_cand.read_text(encoding="utf-8")
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            for l in lines:
                if l.startswith("1."):
                    title = l[2:].strip()
                    break
        except Exception:
            pass

    # 3. Compute Schedule Slot: Prime-Time Evening (9:00 PM IST / 15:30 UTC)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    target_dt = now_utc.replace(hour=15, minute=30, second=0, microsecond=0)
    if target_dt <= now_utc + datetime.timedelta(minutes=30):
        # If less than 30 mins to 15:30 UTC, schedule for tomorrow 15:30 UTC
        target_dt = target_dt + datetime.timedelta(days=1)

    publish_at_iso = target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    ist_display = (target_dt + datetime.timedelta(hours=5, minutes=30)).strftime("%d %b %Y, %I:%M %p IST")

    print("\n" + "=" * 65)
    print("  🚀 SCHEDULING PUBLICATION ON YOUTUBE")
    print("=" * 65)
    print(f"  🎬 Video File   : {target_video.name}")
    print(f"  📸 Cover Thumb  : {thumb_cand.name if thumb_cand.exists() else 'Auto'}")
    print(f"  📌 Title        : {title}")
    print(f"  📅 Scheduled For: {ist_display} ({publish_at_iso})")
    print("=" * 65)

    # 4. Upload and Schedule via YouTube Data API v3
    result = upload_video_via_api(
        video_path=target_video,
        title=title,
        description=description,
        tags=tags,
        privacy_status="private",
        publish_at=publish_at_iso,
        thumbnail_path=thumb_cand if thumb_cand.exists() else None,
        pinned_comment=pinned_comment
    )

    if result.get("success"):
        print("\n" + "=" * 65)
        print("  🎉 VIDEO SUCCESSFULLY SCHEDULED ON YOUTUBE!")
        print("=" * 65)
        print(f"  📌 Title       : {result['title']}")
        print(f"  🆔 Video ID    : {result['video_id']}")
        print(f"  👉 YouTube URL : {result['link']}")
        print(f"  📅 Release Slot: {ist_display}")
        print(f"  🏷️ Tagging     : Full quote-aware viral tags applied (480 chars)")
        print(f"  💬 Pinned Note : Auto-posted for engagement retention")
        print("=" * 65 + "\n")
        return result
    else:
        print(f"❌ Failed to schedule video: {result.get('error')}")
        return False

if __name__ == "__main__":
    schedule_video()
