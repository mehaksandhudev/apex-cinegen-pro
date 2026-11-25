"""
Sheru Bhai Automated Telegram Bot Controller & Mobile Studio
Inspired by the production-tested architecture of the Telegram Studio Bot.

Features:
- Native Inline Keyboard Action Buttons (Zero typing required on mobile)
- Auto-registered Telegram Slash Commands (Instant autocomplete in Telegram app)
- Interactive Callback Handlers for 1-tap generation, batch, upload & credits
- Real-time milestone progress notifications delivered to chat
- Delivers the final 33s video (.mp4), high-res cover thumbnail (.jpg), and viral SEO package
- 1-Tap YouTube Studio Zero-Quota Uploader with direct https://youtu.be/ link generation
- Live Google Flow credit & system health monitor
"""

import os
import sys
import time
import json
import threading
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import (
    BASE_DIR, OUTPUT_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, STUDIO_ACCESS_KEY
)
from banner import print_creator_terminal_banner

# Access Gating & Persistent Authorization
AUTH_USERS_FILE = BASE_DIR / "authorized_users.json"

def load_authorized_users() -> Dict[str, Dict]:
    if AUTH_USERS_FILE.exists():
        try:
            return json.loads(AUTH_USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_authorized_user(chat_id: Any, user_name: str, handle: str = "") -> bool:
    users = load_authorized_users()
    users[str(chat_id)] = {
        "name": user_name,
        "username": handle or "",
        "unlocked_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        AUTH_USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        log(f"Error saving authorized user: {e}")
        return False

def is_user_authorized(chat_id: Any) -> bool:
    if TELEGRAM_CHAT_ID and str(chat_id) == str(TELEGRAM_CHAT_ID):
        return True
    users = load_authorized_users()
    return str(chat_id) in users

# Current execution state
CURRENT_STATE = {
    "is_busy": False,
    "current_task": "Idle",
    "progress": "",
    "last_video": None,
    "last_link": None
}

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] [TelegramBot] {msg}", flush=True)

class TelegramStudioBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.admin_chat_id = TELEGRAM_CHAT_ID or None

    def api_call(self, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None, timeout: int = 35) -> Dict:
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if files:
                    resp = requests.post(url, data=data or {}, files=files, timeout=timeout)
                else:
                    resp = requests.post(url, json=data or {}, timeout=timeout)
                return resp.json()
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.8)
                    continue
                log(f"API {endpoint} error: {e}")
                return {"ok": False, "error": str(e)}

    def send_message(self, chat_id: Any, text: str, reply_markup: Optional[Dict] = None) -> Dict:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self.api_call("sendMessage", payload)
        if not res.get("ok"):
            # Plaintext fallback if HTML formatting had special characters
            payload["parse_mode"] = None
            res = self.api_call("sendMessage", payload)
        return res

    def send_photo(self, chat_id: Any, photo_path: Path, caption: str = "", reply_markup: Optional[Dict] = None) -> Dict:
        if not photo_path.exists():
            return self.send_message(chat_id, caption, reply_markup)
        with open(photo_path, "rb") as f:
            data = {"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            return self.api_call("sendPhoto", data=data, files={"photo": f}, timeout=60)

    def send_video(self, chat_id: Any, video_path: Path, caption: str = "", thumb_path: Optional[Path] = None, reply_markup: Optional[Dict] = None) -> Dict:
        if not video_path.exists():
            return self.send_message(chat_id, f"Video not found: {video_path}")
        f_vid = open(video_path, "rb")
        files = {"video": (video_path.name, f_vid, "video/mp4")}
        f_thumb = None
        if thumb_path and thumb_path.exists():
            f_thumb = open(thumb_path, "rb")
            files["thumbnail"] = (thumb_path.name, f_thumb, "image/jpeg")
        data = {
            "chat_id": str(chat_id),
            "caption": caption[:1024],
            "supports_streaming": "true",
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        try:
            return self.api_call("sendVideo", data=data, files=files, timeout=180)
        finally:
            f_vid.close()
            if f_thumb:
                f_thumb.close()

    def send_document(self, chat_id: Any, doc_path: Path, caption: str = "") -> Dict:
        if not doc_path.exists():
            return {"ok": False}
        with open(doc_path, "rb") as f:
            return self.api_call("sendDocument", data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}, files={"document": f}, timeout=60)

    def answer_callback(self, callback_query_id: str, text: Optional[str] = None):
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return self.api_call("answerCallbackQuery", payload)

    def setup_bot_commands(self):
        """Registers slash commands with Telegram for instant command autocompletion."""
        commands = [
            {"command": "menu", "description": "Studio Hub & Interactive Action Buttons"},
            {"command": "unlock", "description": "1-Time Studio Access Key (/unlock <key>)"},
            {"command": "stats", "description": "Live YouTube Channel Stats & Subscribers"},
            {"command": "top", "description": "Top Performing Channel Videos"},
            {"command": "comments", "description": "Recent Audience Comments"},
            {"command": "generate", "description": "Produce 1 Fresh Short (/generate <topic>)"},
            {"command": "batch", "description": "Run Continuous Batch (/batch 3)"},
            {"command": "upload", "description": "Upload Latest Video to YouTube Studio"},
            {"command": "credits", "description": "Verify Google Flow Credits Health"},
            {"command": "videos", "description": "View & Upload Recent Videos"},
            {"command": "status", "description": "Live Studio State & Activity"},
            {"command": "help", "description": "Guide & Command Reference"}
        ]
        try:
            res = self.api_call("setMyCommands", {"commands": commands})
            log(f"Registered Telegram slash commands: {res.get('ok')}")
        except Exception as e:
            log(f"Failed to register commands: {e}")

    def get_studio_keyboard(self) -> Dict:
        """Returns the primary mobile keyboard control deck."""
        return {
            "inline_keyboard": [
                [
                    {"text": "📊 Channel Stats", "callback_data": "btn_channel_stats"},
                    {"text": "💳 Check Credits", "callback_data": "btn_credits"}
                ],
                [
                    {"text": "🎬 Generate Story", "callback_data": "btn_generate"},
                    {"text": "⚡ Batch Mode", "callback_data": "btn_batch_menu"}
                ],
                [
                    {"text": "📤 Upload to YouTube", "callback_data": "btn_upload_latest"},
                    {"text": "📹 Recent Videos", "callback_data": "btn_videos"}
                ]
            ]
        }

def run_pipeline_worker(bot: TelegramStudioBot, chat_id, custom_topic: str = None, batch_count: int = 1, upload_yt: bool = False, num_clips: int = 2):
    global CURRENT_STATE
    CURRENT_STATE["is_busy"] = True

    try:
        topic_info = f"'{custom_topic}'" if custom_topic else "Autonomous Viral Selection"
        duration_label = f"{num_clips} Clips ({num_clips * 10}s + Outro)"
        bot.send_message(
            chat_id,
            f"🎬 <b>APEX CINEGEN PRO — PRODUCTION ENGINE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 <b>Lead Architect</b>: Mehak Sandhu (@mehaksandhudev)\n"
            f"🚀 <b>Launching Autonomous Pipeline</b>\n"
            f"• <b>Format</b>: {duration_label}\n"
            f"• <b>Batch Count</b>: {batch_count}\n"
            f"• <b>Topic</b>: {topic_info}\n"
            f"• <b>YouTube Studio</b>: {'Direct CDP Publishing' if upload_yt else 'Offline Render'}\n\n"
            f"<i>Live milestone telemetry active...</i>"
        )

        cmd = [sys.executable, "-u", str(BASE_DIR / "run_all.py"), "--clips", str(num_clips)]
        if batch_count > 1:
            cmd.extend(["--batch", str(batch_count)])
        if custom_topic:
            cmd.extend(["--topic", custom_topic])
        if upload_yt:
            cmd.append("--upload")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(BASE_DIR)
        )

        total_steps = 7 if num_clips == 3 else 6
        sent_steps = set()
        output_lines = []
        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue
            output_lines.append(clean_line)
            print(f"  [Worker] {clean_line}")

            if "GATE" in clean_line or "Step" in clean_line:
                CURRENT_STATE["current_task"] = clean_line
            if "progress:" in clean_line or "rendering:" in clean_line:
                CURRENT_STATE["progress"] = clean_line

            # Dynamic milestone alerts (1/6..6/6 for 2-clip, 1/7..7/7 for 3-clip)
            if ("[Step 1]" in clean_line or "[Step 2]" in clean_line) and "s1" not in sent_steps:
                sent_steps.add("s1")
                bot.send_message(chat_id, f"💡 <b>[Step 1/{total_steps}] Brainstorming {num_clips * 10}s Story & Gemini Evaluation...</b>")
            elif "[Step 4]" in clean_line and "s2" not in sent_steps:
                sent_steps.add("s2")
                bot.send_message(chat_id, f"🎬 <b>[Step 2/{total_steps}] Rendering Clip 1 (Google Flow 10s)...</b>")
            elif "[Step 5]" in clean_line and "Clip 2" in clean_line and "s3" not in sent_steps:
                sent_steps.add("s3")
                bot.send_message(chat_id, f"⏱️ <b>[Step 3/{total_steps}] Extending Clip 2 (10s Extension, Total 20s)...</b>")
            elif "[Step 5]" in clean_line and "Clip 3" in clean_line and "s4" not in sent_steps:
                sent_steps.add("s4")
                bot.send_message(chat_id, f"🎞️ <b>[Step 4/{total_steps}] Extending Clip 3 (10s Extension, Total 30s)...</b>")
            elif "[Step 6]" in clean_line and "sdl" not in sent_steps:
                sent_steps.add("sdl")
                dl_idx = 5 if num_clips == 3 else 4
                bot.send_message(chat_id, f"⚡ <b>[Step {dl_idx}/{total_steps}] 720p Download & Local Outro Stitching...</b>")
            elif ("Thumbnails" in clean_line or "Generating Viral Metadata" in clean_line) and "sseo" not in sent_steps:
                sent_steps.add("sseo")
                seo_idx = 6 if num_clips == 3 else 5
                bot.send_message(chat_id, f"🖼️ <b>[Step {seo_idx}/{total_steps}] Extracting Cover Thumbnails & Viral SEO...</b>")

        process.wait()

        if process.returncode == 0:
            recent_mp4s = sorted(OUTPUT_DIR.glob("sheru_final_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if recent_mp4s:
                latest_video = recent_mp4s[0]
                CURRENT_STATE["last_video"] = latest_video

                base_stem = latest_video.stem
                thumb_path = OUTPUT_DIR / f"{base_stem}_thumbnail.jpg"
                info_path = OUTPUT_DIR / f"{base_stem}_info.txt"

                caption_title = "Sheru Bhai Revenge Flex"
                if info_path.exists():
                    try:
                        info_text = info_path.read_text(encoding="utf-8")
                        lines = [l.strip() for l in info_text.splitlines() if l.strip()]
                        for l in lines:
                            if l.startswith("1."):
                                caption_title = l[2:].strip()
                                break
                    except Exception:
                        pass

                yt_link = ""
                for line in output_lines:
                    if "youtu.be" in line or "youtube.com/shorts" in line or "studio.youtube.com" in line:
                        yt_link = line.split("--> Link:")[-1].strip() if "--> Link:" in line else line.strip()

                bot.send_message(chat_id, f"✅ <b>[Step {total_steps}/{total_steps}] All Steps Complete! Sending Your Video...</b>")

                approx_sec = f"{num_clips * 10 + 10}s"
                post_kb = {
                    "inline_keyboard": [
                        [
                            {"text": "🚀 Approve & Schedule (9 PM IST)", "callback_data": f"approve_sched:{latest_video.name}"},
                            {"text": "🏷️ View Tags & Info", "callback_data": f"view_meta:{latest_video.name}"}
                        ],
                        [
                            {"text": "📸 Send Thumbnail & Docs", "callback_data": f"send_assets:{latest_video.name}"},
                            {"text": "📤 Publish Instantly", "callback_data": f"publish_now:{latest_video.name}"}
                        ],
                        [
                            {"text": "📹 All Videos", "callback_data": "btn_videos"},
                            {"text": "🎬 Generate Another", "callback_data": "btn_generate"}
                        ]
                    ]
                }
                bot.send_video(
                    chat_id,
                    latest_video,
                    caption=f"🔥 <b>{caption_title}</b>\n⏱️ ~{approx_sec} 720p | Ready for YouTube Shorts & Reels\n\n👇 <i>Watch above, or tap below for Thumbnail, Tags, or YouTube Scheduling:</i>",
                    thumb_path=thumb_path if thumb_path.exists() else None,
                    reply_markup=post_kb
                )

                if yt_link:
                    bot.send_message(
                        chat_id,
                        f"🎉 <b>YouTube Upload Successful!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👉 <b>Watch Short:</b> {yt_link}"
                    )
            else:
                bot.send_message(chat_id, "⚠️ Pipeline finished, but no MP4 found in output.")
        else:
            bot.send_message(
                chat_id,
                f"❌ <b>Pipeline exited with code {process.returncode}</b>\n"
                f"<code>{chr(10).join(output_lines[-4:])}</code>"
            )

    except Exception as e:
        bot.send_message(chat_id, f"❌ <b>Pipeline Error</b>: {str(e)}")
    finally:
        CURRENT_STATE["is_busy"] = False
        CURRENT_STATE["current_task"] = "Idle"

def handle_check_credits(bot: TelegramStudioBot, chat_id: Any):
    bot.send_message(chat_id, "💳 <i>Querying Google Flow live credit telemetry...</i>")
    details = None
    try:
        from playwright.sync_api import sync_playwright
        from flow_credits import get_exact_credit_details
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            flow_pages = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url]
            if flow_pages:
                details = get_exact_credit_details(flow_pages[0])
    except Exception:
        pass

    if not details or not details.get("success"):
        from flow_credits import get_exact_credit_details
        details = get_exact_credit_details(flow_page=None)

    if details and details.get("credits") is not None:
        user_line = f"• 👤 <b>Account</b>: {details.get('user', 'Mehak Sandhu')} ({details.get('email', 'mehaksandhudev@gmail.com')})\n"
        reset_line = f"• 🔄 <b>Next Reset</b>: {details.get('reset_date', 'Dec 7 at 12:46 AM')}\n"
        est_clips = details['credits'] // 2
        cached_tag = " <i>(Cached Sync)</i>" if details.get("cached") else " <i>(Live)</i>"

        msg = (
            f"💳 <b>GOOGLE FLOW CREDITS TELEMETRY</b>{cached_tag}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{user_line}"
            f"• 💎 <b>Plan</b>: Google Flow {details.get('tier', 'PRO')} Tier\n"
            f"• ⚡ <b>Available Balance</b>: <b>{details['credits']} Credits</b>\n"
            f"{reset_line}"
            f"• 🎬 <b>Estimated Capacity</b>: ~{est_clips} full video generations\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <i>Compute engine operational and ready for batch runs.</i>"
        )
        bot.send_message(chat_id, msg, reply_markup=bot.get_studio_keyboard())
    else:
        bot.send_message(
            chat_id,
            "⚠️ Could not verify credits balance at this moment.",
            reply_markup=bot.get_studio_keyboard()
        )

def handle_channel_stats(bot: TelegramStudioBot, chat_id: Any):
    try:
        from youtube_api import get_channel_telemetry
        info = get_channel_telemetry()
        if info.get("connected"):
            custom = f" ({info['custom_url']})" if info.get("custom_url") else ""
            msg = (
                f"📊 <b>OFFICIAL YOUTUBE CHANNEL TELEMETRY</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📺 <b>Channel:</b> {info['title']}{custom}\n"
                f"👥 <b>Subscribers:</b> {info['subscribers']:,}\n"
                f"👀 <b>Total Channel Views:</b> {info['views']:,}\n"
                f"🎬 <b>Published Videos:</b> {info['video_count']}\n"
                f"🆔 <b>Channel ID:</b> <code>{info['channel_id']}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔐 <b>OAuth Status:</b> Active & Synchronized\n"
                f"⚡ <i>Data queried directly via YouTube Data API v3.</i>"
            )
            bot.send_message(chat_id, msg, reply_markup=bot.get_studio_keyboard())
        else:
            err = info.get("error", "Not authenticated")
            msg = (
                f"⚠️ <b>YouTube OAuth Not Linked</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Your channel OAuth token is not yet active.\n\n"
                f"👉 <b>How to connect in 10 seconds:</b>\n"
                f"Double-click <code>connect_youtube_channel.bat</code> on your PC.\n"
                f"Your browser will open to select your Google Account, and the token will save automatically!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Details: {err}</i>"
            )
            bot.send_message(chat_id, msg, reply_markup=bot.get_studio_keyboard())
    except Exception as ex:
        bot.send_message(chat_id, f"❌ Failed to query YouTube API: {ex}")

def handle_top_videos(bot: TelegramStudioBot, chat_id: Any):
    try:
        from youtube_api import get_top_videos
        top_vids = get_top_videos(limit=5)
        if not top_vids:
            bot.send_message(chat_id, "ℹ️ No published videos found on your YouTube channel yet, or OAuth token needs linking.")
            return

        lines = ["🏆 <b>CHANNEL TOP PERFORMING VIDEOS</b>", "━━━━━━━━━━━━━━━━━━━━"]
        for i, v in enumerate(top_vids, 1):
            lines.append(f"<b>{i}. {v['title']}</b>")
            lines.append(f"   👀 {v['views']:,} views • 👍 {v['likes']:,} likes")
            lines.append(f"   👉 {v['url']}\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        bot.send_message(chat_id, "\n".join(lines), reply_markup=bot.get_studio_keyboard())
    except Exception as ex:
        bot.send_message(chat_id, f"❌ Error fetching top videos: {ex}")

def handle_recent_comments(bot: TelegramStudioBot, chat_id: Any):
    try:
        from youtube_api import get_recent_comments
        comments = get_recent_comments(limit=5)
        if not comments:
            bot.send_message(chat_id, "ℹ️ No recent comments found on your YouTube channel yet.")
            return

        lines = ["💬 <b>RECENT AUDIENCE COMMENTS</b>", "━━━━━━━━━━━━━━━━━━━━"]
        for c in comments:
            lines.append(f"👤 <b>{c['author']}</b>: {c['text'][:120]}")
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        bot.send_message(chat_id, "\n".join(lines), reply_markup=bot.get_studio_keyboard())
    except Exception as ex:
        bot.send_message(chat_id, f"❌ Error fetching comments: {ex}")

def get_video_metadata(video_path: Path) -> dict:
    stem = video_path.stem
    info_candidates = [
        OUTPUT_DIR / f"{stem}_info.txt",
        OUTPUT_DIR / f"{stem}_info.json",
        OUTPUT_DIR / "sheru_cheetah_flying_pind_info.txt"
    ]
    thumb_candidates = [
        OUTPUT_DIR / f"{stem}_thumbnail.jpg",
        OUTPUT_DIR / f"{stem}_thumbnail.png",
        OUTPUT_DIR / "sheru_cheetah_flying_pind_thumbnail.jpg"
    ]
    thumb_path = None
    for tc in thumb_candidates:
        if tc.exists():
            thumb_path = tc
            break

    # Defaults
    clean_name = stem.replace("sheru_", "").replace("_", " ").title()
    title = f"{clean_name} 💥 Sheru Bhai Comedy #shorts"
    description = f"{clean_name} - Sheru Bhai returns with next-level swag and flex! #SheruBhai #Shorts #Comedy #Reels"
    pinned_comment = "Sheru Bhai ka yeh episode kaisa laga? Comment karke batao! 👇"
    tags = [
        "Sheru Bhai", "Sheru Comedy", "Hindi Comedy", "Funny Video",
        "Indian Animation", "Animal Comedy", "Desi Comedy", "YouTube Shorts",
        "Shorts", "Trending Shorts", "Viral Shorts", "Comedy Shorts", "Ghanta",
        "Attitude Status", "Billionaire Flex", "Gold Chain Lion", "Viral Comedy",
        "Punjab Comedy", "Reels"
    ]

    for ic in info_candidates:
        if ic.exists():
            try:
                content = ic.read_text(encoding="utf-8")
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                for l in lines:
                    if l.startswith("1."):
                        title = l[2:].strip()
                        break
                if "[POST DESCRIPTION]" in content:
                    parts = content.split("[POST DESCRIPTION]")[1].split("[PINNED COMMENT")[0]
                    description = parts.strip()
                if "[PINNED COMMENT" in content:
                    parts = content.split("[PINNED COMMENT")[1].split("[HASHTAGS]")[0]
                    pinned_comment = parts.replace("(DRIVES ENGAGEMENT)]", "").strip()
                break
            except Exception:
                pass

    return {
        "title": title,
        "description": description,
        "pinned_comment": pinned_comment,
        "tags": tags,
        "thumbnail": thumb_path
    }

def handle_videos_menu(bot: TelegramStudioBot, chat_id: Any):
    videos = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if not videos:
        bot.send_message(chat_id, "ℹ️ No generated videos found in output folder yet.", reply_markup=bot.get_studio_keyboard())
        return

    buttons = []
    text_lines = ["🎬 <b>RECENT GENERATED EPISODES</b>", "━━━━━━━━━━━━━━━━━━━━"]
    text_lines.append("Tap any episode below to <b>Watch & Stream</b> directly in Telegram, review tags, or schedule:")
    text_lines.append("")

    for i, v in enumerate(videos, 1):
        mb = v.stat().st_size / (1024 * 1024)
        meta = get_video_metadata(v)
        short_title = meta["title"].replace(" #shorts", "").replace(" #Shorts", "")
        if len(short_title) > 28:
            short_title = short_title[:25] + "..."
        text_lines.append(f"<b>{i}. {meta['title']}</b>\n   📁 <code>{v.name}</code> ({mb:.1f} MB)")
        buttons.append([{"text": f"▶️ Watch #{i}: {short_title} ({mb:.1f}MB)", "callback_data": f"watch:{v.name}"}])

    buttons.append([
        {"text": "🚀 Quick-Schedule Latest", "callback_data": f"approve_sched:{videos[0].name}"},
        {"text": "🏷️ Latest Tags", "callback_data": f"view_meta:{videos[0].name}"}
    ])
    buttons.append([{"text": "🔙 Studio Main Menu", "callback_data": "btn_menu"}])

    text_lines.append("━━━━━━━━━━━━━━━━━━━━")
    bot.send_message(chat_id, "\n".join(text_lines), reply_markup={"inline_keyboard": buttons})

def handle_send_single_video(bot: TelegramStudioBot, chat_id: Any, video_name: str):
    video_path = OUTPUT_DIR / video_name
    if not video_path.exists():
        bot.send_message(chat_id, f"❌ Video file not found: <code>{video_name}</code>")
        return

    meta = get_video_metadata(video_path)
    mb = video_path.stat().st_size / (1024 * 1024)

    caption = (
        f"🎬 <b>{meta['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ <b>Duration:</b> 33.0s (Clip 1 + Clip 2 + Outro)\n"
        f"📦 <b>Size:</b> {mb:.1f} MB • 🎞️ <b>Format:</b> 720x1280 9:16 Vertical\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>Watch above! Then approve, schedule, or view tags below:</i>"
    )

    kb = {
        "inline_keyboard": [
            [
                {"text": "🚀 Approve & Schedule (9 PM IST)", "callback_data": f"approve_sched:{video_path.name}"},
                {"text": "🏷️ View Tags & Info", "callback_data": f"view_meta:{video_path.name}"}
            ],
            [
                {"text": "📤 Publish Instantly (Public)", "callback_data": f"publish_now:{video_path.name}"},
                {"text": "📹 Back to Videos", "callback_data": "btn_videos"}
            ]
        ]
    }

    bot.send_message(chat_id, f"📹 <i>Uploading '{meta['title']}' for direct playback in Telegram...</i>")
    res = bot.send_video(chat_id, video_path, caption=caption, thumb_path=meta["thumbnail"], reply_markup=kb)
    if not res.get("ok"):
        bot.send_message(
            chat_id,
            f"🎬 <b>{meta['title']}</b>\n"
            f"📁 <code>{video_path.name}</code> ({mb:.1f} MB)\n"
            f"ℹ️ Ready on disk. Choose your publishing action:",
            reply_markup=kb
        )

def handle_view_metadata(bot: TelegramStudioBot, chat_id: Any, video_name: str):
    video_path = OUTPUT_DIR / video_name
    meta = get_video_metadata(video_path)
    from youtube_api import pack_youtube_tags_to_limit, VIRAL_SHERU_TAGS

    candidate_tags = meta["tags"] + VIRAL_SHERU_TAGS
    packed_tags = pack_youtube_tags_to_limit(candidate_tags, max_limit=480)
    chars = sum(len(t) for t in packed_tags) + len(packed_tags) * 3

    desc_preview = meta['description'][:220] + "..." if len(meta['description']) > 220 else meta['description']

    msg = (
        f"🏷️ <b>EPISODE METADATA & VIRAL SEO TAGS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>File:</b> <code>{video_name}</code>\n"
        f"📌 <b>Title:</b>\n<code>{meta['title']}</code>\n\n"
        f"📝 <b>Description:</b>\n<i>{desc_preview}</i>\n\n"
        f"🏷️ <b>Packed Viral Tags ({len(packed_tags)} tags • ~{chars}/500 chars):</b>\n"
        f"<code>{', '.join(packed_tags)}</code>\n\n"
        f"💬 <b>Pinned Retention Comment:</b>\n<i>\"{meta['pinned_comment']}\"</i>\n\n"
        f"📅 <b>Prime-Time Slot:</b> Tonight at 09:00 PM IST (15:30 UTC)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>Ready to release this video?</i>"
    )

    kb = {
        "inline_keyboard": [
            [
                {"text": "🚀 Approve & Schedule (9 PM IST)", "callback_data": f"approve_sched:{video_path.name}"},
                {"text": "📤 Publish Instantly", "callback_data": f"publish_now:{video_path.name}"}
            ],
            [
                {"text": "▶️ Watch Video", "callback_data": f"watch:{video_path.name}"},
                {"text": "📹 All Videos", "callback_data": "btn_videos"}
            ]
        ]
    }
    bot.send_message(chat_id, msg, reply_markup=kb)

def handle_approve_and_schedule(bot: TelegramStudioBot, chat_id: Any, video_name: str, privacy_status: str = "private", schedule: bool = True):
    video_path = OUTPUT_DIR / video_name
    if not video_path.exists():
        recent_mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if recent_mp4s:
            video_path = recent_mp4s[0]
        else:
            bot.send_message(chat_id, f"❌ Video file not found: <code>{video_name}</code>")
            return

    meta = get_video_metadata(video_path)
    mode_text = "Scheduling for 09:00 PM IST Prime-Time" if schedule else "Publishing Instantly (Public)"
    bot.send_message(chat_id, f"⏳ <i>{mode_text} for '{meta['title']}' via YouTube Data API v3...</i>")

    def _task():
        try:
            import datetime
            from youtube_api import upload_video_via_api

            publish_at_iso = None
            ist_display = "Immediate Public Release"
            if schedule:
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                target_dt = now_utc.replace(hour=15, minute=30, second=0, microsecond=0)
                if target_dt <= now_utc + datetime.timedelta(minutes=30):
                    target_dt = target_dt + datetime.timedelta(days=1)
                publish_at_iso = target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                ist_display = (target_dt + datetime.timedelta(hours=5, minutes=30)).strftime("%d %b %Y, %I:%M %p IST")

            res = upload_video_via_api(
                video_path=video_path,
                title=meta["title"],
                description=meta["description"],
                tags=meta["tags"],
                privacy_status=privacy_status,
                publish_at=publish_at_iso,
                thumbnail_path=meta["thumbnail"],
                pinned_comment=meta["pinned_comment"]
            )

            if res.get("success"):
                card = (
                    f"🎉 <b>YOUTUBE RELEASE CONFIRMED!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📌 <b>Title:</b> {res['title']}\n"
                    f"🆔 <b>Video ID:</b> <code>{res['video_id']}</code>\n"
                    f"👉 <b>Watch / Preview Link:</b> {res['link']}\n"
                    f"📅 <b>Release Slot:</b> <b>{ist_display}</b>\n"
                    f"🏷️ <b>Viral Tags:</b> Full quote-aware tags packed (480 chars)\n"
                    f"📸 <b>Thumbnail:</b> Custom cover uploaded\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 <b>Lead Architect:</b> Mehak Sandhu (@mehaksandhudev)\n"
                    f"⚡ <i>Channel: The Quiet Schema (@thequietschema)</i>"
                )
                bot.send_message(chat_id, card, reply_markup=bot.get_studio_keyboard())
            else:
                bot.send_message(chat_id, f"❌ Failed to release video: {res.get('error')}", reply_markup=bot.get_studio_keyboard())
        except Exception as ex:
            bot.send_message(chat_id, f"❌ Publishing exception: {ex}", reply_markup=bot.get_studio_keyboard())

    t = threading.Thread(target=_task)
    t.daemon = True
    t.start()

def handle_upload_action(bot: TelegramStudioBot, chat_id: Any, video_name: Optional[str] = None):
    recent_mp4s = sorted(OUTPUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not recent_mp4s:
        bot.send_message(chat_id, "❌ No videos found in output folder to upload.")
        return
    target_name = video_name or recent_mp4s[0].name
    handle_approve_and_schedule(bot, chat_id, target_name, privacy_status="private", schedule=True)

def main():
    print_creator_terminal_banner(project_name="APEX CINEGEN — TELEGRAM STUDIO CONTROLLER")
    token = TELEGRAM_BOT_TOKEN
    if not token:
        print("\n[!] TELEGRAM_BOT_TOKEN missing in config.py")
        sys.exit(1)

    bot = TelegramStudioBot(token)
    bot.setup_bot_commands()

    print("\n  [✓] Telegram Bot @sheruautobot listening for mobile commands & button taps...")
    print("  [✓] Token verified. Production protocol active!\n")

    offset = None
    while True:
        try:
            updates = bot.api_call("getUpdates", {"offset": offset, "timeout": 20}, timeout=25).get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1

                # Handle Button Callbacks
                if "callback_query" in upd:
                    cb = upd["callback_query"]
                    cb_id = cb["id"]
                    data = cb.get("data", "")
                    chat_id = cb["message"]["chat"]["id"]

                    bot.answer_callback(cb_id, text="Processing command...")

                    if not is_user_authorized(chat_id):
                        bot.send_message(
                            chat_id,
                            f"🔒 <b>APEX CINEGEN PRO — ACCESS GATED</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"👑 <b>Studio Owner:</b> Mehak Sandhu (@mehaksandhudev)\n\n"
                            f"This private AI cinema bot is access-restricted.\n"
                            f"Please enter your 1-time <b>Studio Access Key</b> to unlock control:\n\n"
                            f"👉 Type: <code>/unlock &lt;key&gt;</code>\n"
                            f"<i>(Or simply send the access key directly here)</i>"
                        )
                        continue

                    if data == "btn_generate":
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            kb = {
                                "inline_keyboard": [
                                    [{"text": "🎬 2 Clips (20s + Outro) • Fast", "callback_data": "gen_mode:2"}],
                                    [{"text": "🎞️ 3 Clips (30s + Outro) • Epic", "callback_data": "gen_mode:3"}],
                                    [{"text": "🔙 Back to Menu", "callback_data": "btn_menu"}]
                                ]
                            }
                            bot.send_message(
                                chat_id,
                                "🎬 <b>SELECT STORY LENGTH</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━\n"
                                "• <b>2 Clips (20s + Outro):</b> Fast ~30s Short\n"
                                "• <b>3 Clips (30s + Outro):</b> Extended ~40s Epic Short\n\n"
                                "👇 <i>Choose format to start generation:</i>",
                                reply_markup=kb
                            )

                    elif data.startswith("gen_mode:"):
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            num_clips = int(data.split("gen_mode:")[-1])
                            t = threading.Thread(target=run_pipeline_worker, args=(bot, chat_id, None, 1, False, num_clips))
                            t.daemon = True
                            t.start()

                    elif data == "btn_batch_menu":
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            kb = {
                                "inline_keyboard": [
                                    [
                                        {"text": "2 Videos", "callback_data": "batch_count:2"},
                                        {"text": "3 Videos", "callback_data": "batch_count:3"},
                                        {"text": "5 Videos", "callback_data": "batch_count:5"}
                                    ],
                                    [
                                        {"text": "7 Videos", "callback_data": "batch_count:7"},
                                        {"text": "10 Videos", "callback_data": "batch_count:10"}
                                    ],
                                    [{"text": "🔙 Back to Menu", "callback_data": "btn_menu"}]
                                ]
                            }
                            bot.send_message(
                                chat_id,
                                "⚡ <b>FLEXIBLE BATCH GENERATOR</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━\n"
                                "How many videos do you want to generate in this batch?\n"
                                "<i>(Tip: You can also type <code>/batch 4</code> for any custom number!)</i>",
                                reply_markup=kb
                            )

                    elif data.startswith("batch_count:"):
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            b_cnt = int(data.split("batch_count:")[-1])
                            kb = {
                                "inline_keyboard": [
                                    [{"text": f"🎬 {b_cnt}x Videos • 2 Clips Each (20s + Outro)", "callback_data": f"run_batch:{b_cnt}:2"}],
                                    [{"text": f"🎞️ {b_cnt}x Videos • 3 Clips Each (30s + Outro)", "callback_data": f"run_batch:{b_cnt}:3"}],
                                    [{"text": "🔙 Change Count", "callback_data": "btn_batch_menu"}]
                                ]
                            }
                            bot.send_message(
                                chat_id,
                                f"⚡ <b>BATCH SIZE: {b_cnt} VIDEOS</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"Now choose the clip format for all <b>{b_cnt}</b> videos:",
                                reply_markup=kb
                            )

                    elif data.startswith("run_batch:"):
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            parts = data.split(":")
                            b_cnt = int(parts[1])
                            num_clips = int(parts[2])
                            t = threading.Thread(target=run_pipeline_worker, args=(bot, chat_id, None, b_cnt, False, num_clips))
                            t.daemon = True
                            t.start()

                    elif data == "btn_batch_3":
                        if CURRENT_STATE["is_busy"]:
                            bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        else:
                            t = threading.Thread(target=run_pipeline_worker, args=(bot, chat_id, None, 3, False, 2))
                            t.daemon = True
                            t.start()

                    elif data == "btn_upload_latest":
                        handle_upload_action(bot, chat_id)

                    elif data == "btn_credits":
                        handle_check_credits(bot, chat_id)

                    elif data == "btn_channel_stats":
                        handle_channel_stats(bot, chat_id)

                    elif data == "btn_status":
                        status_text = (
                            f"📊 <b>Studio Telemetry</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"• <b>Status</b>: {'🟡 In Production' if CURRENT_STATE['is_busy'] else '🟢 Idle & Ready'}\n"
                            f"• <b>Active Task</b>: {CURRENT_STATE['current_task']}\n"
                            f"• <b>Render Progress</b>: {CURRENT_STATE.get('progress') or 'N/A'}\n"
                            f"• <b>Last File</b>: {CURRENT_STATE['last_video'].name if CURRENT_STATE['last_video'] else 'None'}"
                        )
                        bot.send_message(chat_id, status_text, reply_markup=bot.get_studio_keyboard())

                    elif data == "btn_videos":
                        handle_videos_menu(bot, chat_id)

                    elif data == "btn_menu":
                        welcome_text = (
                            f"🎬 <b>APEX CINEGEN PRO — AUTONOMOUS STUDIO</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"👑 <b>Lead Architect</b>: Mehak Sandhu (@mehaksandhudev)\n\n"
                            f"⚡ <b>Select an action from your mobile control deck:</b>"
                        )
                        bot.send_message(chat_id, welcome_text, reply_markup=bot.get_studio_keyboard())

                    elif data.startswith("watch:"):
                        v_name = data.split("watch:")[-1]
                        handle_send_single_video(bot, chat_id, v_name)

                    elif data.startswith("view_meta:"):
                        v_name = data.split("view_meta:")[-1]
                        handle_view_metadata(bot, chat_id, v_name)

                    elif data.startswith("send_assets:"):
                        v_name = data.split("send_assets:")[-1]
                        v_path = OUTPUT_DIR / v_name
                        t_path = OUTPUT_DIR / f"{v_path.stem}_thumbnail.jpg"
                        i_path = OUTPUT_DIR / f"{v_path.stem}_info.txt"
                        meta = get_video_metadata(v_path)
                        if t_path.exists():
                            bot.send_photo(chat_id, t_path, caption=f"📸 <b>High-Res Cover Thumbnail</b>\n<code>{meta['title']}</code>")
                        if i_path.exists():
                            bot.send_document(chat_id, i_path, caption="📋 <b>Viral Metadata Package (Titles, Description, Pinned Comment & Tags)</b>")
                        if not t_path.exists() and not i_path.exists():
                            bot.send_message(chat_id, "ℹ️ Thumbnail/metadata files not found for this video.")

                    elif data.startswith("approve_sched:"):
                        v_name = data.split("approve_sched:")[-1]
                        handle_approve_and_schedule(bot, chat_id, v_name, privacy_status="private", schedule=True)

                    elif data.startswith("publish_now:"):
                        v_name = data.split("publish_now:")[-1]
                        handle_approve_and_schedule(bot, chat_id, v_name, privacy_status="public", schedule=False)

                    elif data.startswith("upload_specific:"):
                        v_name = data.split("upload_specific:")[-1]
                        handle_approve_and_schedule(bot, chat_id, v_name, privacy_status="private", schedule=True)

                    continue

                # Handle Text Messages & Slash Commands
                msg = upd.get("message")
                if not msg or "text" not in msg:
                    continue

                chat_id = msg["chat"]["id"]
                text = msg["text"].strip()
                user_name = msg["from"].get("first_name", "Creator")
                user_handle = msg["from"].get("username", "")

                log(f"Received command from {user_name} (@{user_handle}, {chat_id}): '{text}'")

                # 1. Check if user is attempting to unlock with access key
                is_unlock_attempt = False
                key_candidate = ""
                if text.startswith("/unlock"):
                    parts = text.split("/unlock", 1)
                    key_candidate = parts[1].strip()
                    is_unlock_attempt = True
                elif text.startswith("/start") and len(text.split()) > 1:
                    key_candidate = text.split()[1].strip()
                    is_unlock_attempt = True
                elif not is_user_authorized(chat_id):
                    # For locked users, typing the code directly as a message works!
                    key_candidate = text
                    is_unlock_attempt = True

                if is_unlock_attempt and key_candidate:
                    expected = STUDIO_ACCESS_KEY.strip()
                    if key_candidate.lower() == expected.lower():
                        save_authorized_user(chat_id, user_name, user_handle)
                        unlocked_msg = (
                            f"🎉 <b>ACCESS GRANTED! WELCOME TO APEX CINEGEN PRO</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"👑 <b>Studio Owner</b>: Mehak Sandhu (@mehaksandhudev)\n\n"
                            f"Welcome, <b>{user_name}</b>! Your account has been permanently authenticated.\n"
                            f"You now have full 24/7 studio control over AI video generation and YouTube publishing!\n\n"
                            f"⚡ <b>Tap any button below to start creating:</b>"
                        )
                        bot.send_message(chat_id, unlocked_msg, reply_markup=bot.get_studio_keyboard())
                        continue
                    elif text.startswith("/unlock") or (not is_user_authorized(chat_id) and not text.startswith("/")):
                        bot.send_message(
                            chat_id,
                            f"❌ <b>Invalid Access Key!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"The key you entered is incorrect.\n"
                            f"Please obtain the 1-time Studio Access Key from Mehak Sandhu (@mehaksandhudev).\n\n"
                            f"👉 Type: <code>/unlock &lt;key&gt;</code>"
                        )
                        continue

                # 2. Gatekeeper: If user is not authorized, block any interaction
                if not is_user_authorized(chat_id):
                    gate_msg = (
                        f"🔒 <b>APEX CINEGEN PRO — ACCESS GATED</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👑 <b>Studio Owner</b>: Mehak Sandhu (@mehaksandhudev)\n\n"
                        f"Welcome <b>{user_name}</b>! This private generative cinema studio is gated.\n"
                        f"Please enter your 1-time <b>Studio Access Key</b> to unlock control:\n\n"
                        f"👉 Type: <code>/unlock &lt;key&gt;</code>\n"
                        f"<i>(Or simply send the access key directly here)</i>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"💡 <i>You only need to enter this key ONCE. Your account will remain permanently authenticated.</i>"
                    )
                    bot.send_message(chat_id, gate_msg)
                    continue

                if text.startswith("/users"):
                    users = load_authorized_users()
                    u_lines = ["👥 <b>AUTHORIZED STUDIO USERS</b>", "━━━━━━━━━━━━━━━━━━━━"]
                    for uid, uinfo in users.items():
                        handle_str = f" (@{uinfo.get('username')})" if uinfo.get("username") else ""
                        u_lines.append(f"• 👤 <b>{uinfo.get('name', 'User')}</b>{handle_str} [<code>{uid}</code>]")
                        u_lines.append(f"   🔓 Unlocked: {uinfo.get('unlocked_at', 'N/A')}")
                    u_lines.append("━━━━━━━━━━━━━━━━━━━━")
                    u_lines.append(f"🔑 <b>Studio Access Key:</b> <code>{STUDIO_ACCESS_KEY}</code>")
                    bot.send_message(chat_id, "\n".join(u_lines), reply_markup=bot.get_studio_keyboard())
                    continue

                if text.startswith("/start") or text.startswith("/menu"):
                    welcome_text = (
                        f"🎬 <b>APEX CINEGEN PRO — AUTONOMOUS STUDIO</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👑 <b>Lead Architect</b>: Mehak Sandhu (@mehaksandhudev)\n"
                        f"🌐 <b>Engine</b>: Apex CineGen V2 Obsidian Telemetry\n\n"
                        f"Welcome <b>{user_name}</b>! Your 24/7 autonomous generative cinema & YouTube publishing protocol is online.\n\n"
                        f"⚡ <b>Tap any button below to trigger your studio:</b>"
                    )
                    bot.send_message(chat_id, welcome_text, reply_markup=bot.get_studio_keyboard())

                elif text.startswith("/help"):
                    help_text = (
                        f"🎬 <b>APEX CINEGEN PRO — COMMAND DIRECTORY</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👑 <b>Lead Architect</b>: Mehak Sandhu (@mehaksandhudev)\n"
                        f"• <b>/menu</b> - Open the Interactive Action Deck\n"
                        f"• <b>/generate</b> - Produce 1 fresh 8K vertical short\n"
                        f"• <b>/generate &lt;topic&gt;</b> - Produce short on custom topic\n"
                        f"• <b>/batch 3</b> - Continuous 3-episode master cycle\n"
                        f"• <b>/upload</b> - Zero-quota upload to YouTube Studio\n"
                        f"• <b>/credits</b> - Check Google Flow compute units\n"
                        f"• <b>/videos</b> - View & upload recent media\n"
                        f"• <b>/status</b> - Telemetry & pipeline activity"
                    )
                    bot.send_message(chat_id, help_text, reply_markup=bot.get_studio_keyboard())

                elif text.startswith("/status"):
                    status_text = (
                        f"📊 <b>APEX CINEGEN — STUDIO TELEMETRY</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👑 <b>Developer</b>: Mehak Sandhu (@mehaksandhudev)\n"
                        f"• <b>State</b>: {'🟡 In Production' if CURRENT_STATE['is_busy'] else '🟢 Idle & Ready'}\n"
                        f"• <b>Task</b>: {CURRENT_STATE['current_task']}\n"
                        f"• <b>Render</b>: {CURRENT_STATE.get('progress') or 'N/A'}\n"
                        f"• <b>Latest</b>: {CURRENT_STATE['last_video'].name if CURRENT_STATE['last_video'] else 'None'}"
                    )
                    bot.send_message(chat_id, status_text, reply_markup=bot.get_studio_keyboard())

                elif text.startswith("/stats"):
                    handle_channel_stats(bot, chat_id)

                elif text.startswith("/top"):
                    handle_top_videos(bot, chat_id)

                elif text.startswith("/comments"):
                    handle_recent_comments(bot, chat_id)

                elif text.startswith("/credits"):
                    handle_check_credits(bot, chat_id)

                elif text.startswith("/videos"):
                    handle_videos_menu(bot, chat_id)

                elif text.startswith("/upload"):
                    handle_upload_action(bot, chat_id)

                elif text.startswith("/generate"):
                    if CURRENT_STATE["is_busy"]:
                        bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        continue

                    parts = text.split("/generate", 1)
                    raw_arg = parts[1].strip() if len(parts) > 1 and parts[1].strip() else ""
                    num_clips = 2
                    if raw_arg.startswith("3 ") or raw_arg == "3":
                        num_clips = 3
                        raw_arg = raw_arg[1:].strip()
                    custom_topic = raw_arg if raw_arg else None

                    t = threading.Thread(target=run_pipeline_worker, args=(bot, chat_id, custom_topic, 1, False, num_clips))
                    t.daemon = True
                    t.start()

                elif text.startswith("/batch"):
                    if CURRENT_STATE["is_busy"]:
                        bot.send_message(chat_id, f"⚠️ Studio is busy: <i>{CURRENT_STATE['current_task']}</i>")
                        continue

                    parts = text.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        count = max(1, int(parts[1]))
                        if len(parts) >= 3 and parts[2] in ["2", "3"]:
                            num_clips = int(parts[2])
                            t = threading.Thread(target=run_pipeline_worker, args=(bot, chat_id, None, count, False, num_clips))
                            t.daemon = True
                            t.start()
                        else:
                            kb = {
                                "inline_keyboard": [
                                    [{"text": f"🎬 {count}x Videos • 2 Clips Each (20s + Outro)", "callback_data": f"run_batch:{count}:2"}],
                                    [{"text": f"🎞️ {count}x Videos • 3 Clips Each (30s + Outro)", "callback_data": f"run_batch:{count}:3"}],
                                    [{"text": "🔙 Change Count", "callback_data": "btn_batch_menu"}]
                                ]
                            }
                            bot.send_message(
                                chat_id,
                                f"⚡ <b>BATCH SIZE: {count} VIDEOS</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"Choose clip format for all <b>{count}</b> videos:",
                                reply_markup=kb
                            )
                    else:
                        kb = {
                            "inline_keyboard": [
                                [
                                    {"text": "2 Videos", "callback_data": "batch_count:2"},
                                    {"text": "3 Videos", "callback_data": "batch_count:3"},
                                    {"text": "5 Videos", "callback_data": "batch_count:5"}
                                ],
                                [
                                    {"text": "7 Videos", "callback_data": "batch_count:7"},
                                    {"text": "10 Videos", "callback_data": "batch_count:10"}
                                ],
                                [{"text": "🔙 Back to Menu", "callback_data": "btn_menu"}]
                            ]
                        }
                        bot.send_message(
                            chat_id,
                            "⚡ <b>FLEXIBLE BATCH GENERATOR</b>\n"
                            "━━━━━━━━━━━━━━━━━━━━\n"
                            "How many videos do you want to generate in this batch?\n"
                            "<i>(Or type <code>/batch 4</code> for any custom number!)</i>",
                            reply_markup=kb
                        )

                else:
                    bot.send_message(chat_id, "Send /menu or /start to open the interactive studio deck.", reply_markup=bot.get_studio_keyboard())

        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    main()
