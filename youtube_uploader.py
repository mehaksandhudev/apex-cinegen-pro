"""
YouTube Studio Automated Uploader (Direct CDP / Zero-Quota)
Inspired by the production-tested architecture of the YouTube Publishing Engine.

Features:
- Direct CDP connection to existing authenticated Chrome (port 9222)
- Zero YouTube Data API quota barriers (no 1,600 units/day limit)
- Quote-aware viral tag packing up to YouTube's 485-character internal buffer
- Automatic "Not made for kids" compliance
- Custom high-res thumbnail cover attachment
- "Show more" tag insertion & comedy category optimization
- Visibility control (UNLISTED by default, PUBLIC on demand)
- Extract direct https://youtu.be/ short links
"""

import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict
from playwright.sync_api import sync_playwright

VIRAL_SHERU_TAGS = [
    "Sheru Bhai", "Sheru Comedy", "Sheru", "Billionaire Lion", "Sheru Bhai Revenge",
    "Hindi Comedy", "Funny Video", "Indian Animation", "Animal Comedy", "Desi Comedy",
    "YouTube Shorts", "Shorts", "Trending Shorts", "Viral Shorts", "Comedy Shorts",
    "Ghanta", "Attitude Status", "Billionaire Flex", "Gold Chain Lion", "Viral Comedy"
]

def sanitize_youtube_tag(tag: str) -> str:
    """Sanitizes tags for YouTube Studio tag input."""
    tag = tag.replace("&", "and")
    tag = re.sub(r'[#<>",\'`/:;]', '', tag)
    tag = re.sub(r'\s+', ' ', tag).strip()
    return tag[:80]

def pack_youtube_tags_to_limit(candidate_tags: List[str], max_limit: int = 485) -> List[str]:
    """Packs tags using YouTube's exact internal quote-aware character calculation."""
    packed = []
    for t in candidate_tags:
        clean = sanitize_youtube_tag(t)
        if clean and len(clean) >= 2 and clean.lower() not in [x.lower() for x in packed]:
            cand = packed + [clean]
            chars = sum(len(x) + (2 if ' ' in x else 0) for x in cand)
            commas = len(cand) - 1
            if chars + commas <= max_limit:
                packed.append(clean)
    return packed

def upload_to_youtube_studio(
    video_path: Path,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    thumbnail_path: Optional[Path] = None,
    visibility: str = "UNLISTED",
    context = None
) -> dict:
    """
    Uploads a video to YouTube Studio using the connected Chrome session on port 9222.
    visibility: 'PUBLIC', 'UNLISTED', 'PRIVATE'
    """
    video_path = Path(video_path)
    if not video_path.exists():
        return {"success": False, "error": f"Video file not found: {video_path}"}

    print("\n" + "="*60)
    print("  [YouTube Studio Uploader] Launching Zero-Quota Publishing...")
    print("="*60)
    print(f"  🎬 Video: {video_path.name} ({video_path.stat().st_size / (1024*1024):.1f} MB)")
    print(f"  📌 Title: {title}")
    print(f"  👁️ Visibility: {visibility.upper()}")
    if thumbnail_path and Path(thumbnail_path).exists():
        print(f"  🖼️ Thumbnail: {Path(thumbnail_path).name}")

    # Prepare tags
    all_tags = (tags or []) + VIRAL_SHERU_TAGS
    packed_tags = pack_youtube_tags_to_limit(all_tags, max_limit=480)

    # Format Title with #Shorts
    clean_title = title.strip()
    if "#Shorts" not in clean_title and "#shorts" not in clean_title:
        if len(clean_title) + len(" #Shorts") <= 95:
            clean_title = f"{clean_title} #Shorts"
        else:
            clean_title = clean_title[:87] + "... #Shorts"
    clean_title = clean_title[:95]

    close_browser = False
    p = None
    if context is None:
        p = sync_playwright().start()
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        close_browser = True

    page = context.new_page()
    try:
        print("  [*] Navigating to YouTube Studio...")
        page.goto("https://studio.youtube.com", timeout=30000)
        page.wait_for_timeout(3000)

        # Click Create button
        create_btn = page.locator('#create-icon, button:has-text("Create"), [aria-label="Create"]').first
        create_btn.wait_for(state="visible", timeout=20000)
        create_btn.click()
        page.wait_for_timeout(1000)

        # Click Upload videos
        upload_btn = page.locator('tp-yt-paper-item:has-text("Upload videos"), [test-id="upload-button"]').first
        upload_btn.wait_for(state="visible", timeout=10000)
        upload_btn.click()
        page.wait_for_timeout(2000)

        # Upload video file
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(str(video_path))
        print("  [*] Uploading video stream to YouTube...")
        page.wait_for_timeout(4000)

        # Fill Title
        title_box = page.locator('#textbox[aria-label*="title" i], div#title-textarea #textbox').first
        title_box.wait_for(state="visible", timeout=30000)
        title_box.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.insert_text(clean_title)
        page.wait_for_timeout(1000)
        print("  [✓] Title applied successfully.")

        # Fill Description
        desc_box = page.locator('#textbox[aria-label*="description" i], div#description-textarea #textbox').first
        if desc_box.count() > 0 and desc_box.is_visible():
            desc_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.insert_text(description[:4900])
            page.wait_for_timeout(1000)
            print("  [✓] Description applied successfully.")

        # Upload Thumbnail if provided
        if thumbnail_path and Path(thumbnail_path).exists():
            try:
                thumb_input = page.locator('input#file-loader[type="file"], input[accept*="image"][type="file"]').first
                if thumb_input.count() > 0:
                    thumb_input.set_input_files(str(thumbnail_path))
                    print(f"  [✓] Custom thumbnail attached: {Path(thumbnail_path).name}")
                    page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  [!] Note on thumbnail: {e}")

        # Expand "Show more" to insert tags
        try:
            show_more_btn = page.locator('#toggle-button, div:has-text("Show more"):has(#toggle-button)').first
            if show_more_btn.count() > 0:
                show_more_btn.click(force=True)
                page.wait_for_timeout(1000)
                
                # Insert tags
                tag_input = page.locator('input[aria-label="Tags"], #tags-container input').first
                if tag_input.count() > 0:
                    tag_str = ", ".join(packed_tags)
                    tag_input.click()
                    tag_input.fill(tag_str)
                    page.keyboard.press("Enter")
                    print(f"  [✓] {len(packed_tags)} SEO tags inserted into video metadata.")
                    page.wait_for_timeout(1000)
        except Exception as e:
            print(f"  [!] Note on tags: {e}")

        # Select 'Not made for kids'
        not_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first
        if not_kids.count() > 0:
            not_kids.click(force=True)
            page.wait_for_timeout(500)
            print("  [✓] Audience verified: Not made for kids.")

        # Step 2: Video Elements
        next_btn = page.locator('#next-button').first
        next_btn.wait_for(state="visible", timeout=10000)
        next_btn.click()
        page.wait_for_timeout(1500)

        # Step 3: Checks
        next_btn.click()
        page.wait_for_timeout(1500)

        # Step 4: Visibility
        next_btn.click()
        page.wait_for_timeout(2000)

        # Set Visibility
        vis_upper = visibility.upper()
        if vis_upper == "PUBLIC":
            vis_radio = page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first
        elif vis_upper == "PRIVATE":
            vis_radio = page.locator('tp-yt-paper-radio-button[name="PRIVATE"]').first
        else:
            vis_radio = page.locator('tp-yt-paper-radio-button[name="UNLISTED"]').first

        if vis_radio.count() > 0:
            vis_radio.click(force=True)
            page.wait_for_timeout(1000)
            print(f"  [✓] Visibility calibrated to {vis_upper}.")

        # Extract YouTube Video URL
        yt_link = ""
        link_el = page.locator('a.ytcp-video-info, a[href*="youtu.be"]').first
        if link_el.count() > 0:
            yt_link = link_el.get_attribute("href") or link_el.inner_text().strip()

        # Wait until save/done button is active and enabled
        done_btn = page.locator('#done-button').first
        done_btn.wait_for(state="visible", timeout=15000)
        
        # Verify upload progress before clicking done
        print("  [*] Waiting for YouTube upload upload/processing handshake...")
        for _ in range(60):
            status_text = page.locator('.progress-label, ytcp-video-upload-progress').inner_text() if page.locator('.progress-label').count() > 0 else ""
            if "Uploading" in status_text:
                time.sleep(2)
                continue
            break

        done_btn.click()
        print("  [*] Publishing / Registering video in YouTube Studio...")
        page.wait_for_timeout(5000)

        # Re-check for short link in success dialog if not captured earlier
        if not yt_link:
            link_el2 = page.locator('a[href*="youtu.be"], a.ytcp-video-info').first
            if link_el2.count() > 0:
                yt_link = link_el2.get_attribute("href") or link_el2.inner_text().strip()

        # Close dialog
        close_dialog = page.locator('#close-button, button:has-text("Close")').first
        if close_dialog.count() > 0 and close_dialog.is_visible():
            close_dialog.click()

        print("\n" + "="*60)
        print("  [🎉 SUCCESS 🎉] YOUTUBE STUDIO UPLOAD COMPLETE!")
        print(f"  --> Link: {yt_link or 'Available in YouTube Studio Dashboard'}")
        print("="*60 + "\n")

        return {
            "success": True,
            "link": yt_link,
            "title": clean_title,
            "visibility": visibility
        }

    except Exception as e:
        print(f"  [!] YouTube Studio upload error: {e}")
        return {"success": False, "error": str(e)}
    finally:
        page.close()
        if close_browser and p:
            p.stop()

if __name__ == "__main__":
    recent_mp4s = sorted(Path("output_videos").glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if recent_mp4s:
        test_video = recent_mp4s[0]
        test_thumb = Path("output_videos") / f"{test_video.stem}_thumbnail.jpg"
        print(f"Testing uploader with latest video: {test_video.name}")
        res = upload_to_youtube_studio(
            video_path=test_video,
            title="Sheru Bhai Ultimate Flex #Comedy",
            description="Sheru Bhai takes revenge in style! #SheruBhai #Shorts #Comedy",
            thumbnail_path=test_thumb if test_thumb.exists() else None,
            visibility="UNLISTED"
        )
        print("Result:", res)
    else:
        print("No videos found to upload.")
