import os
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

from config import (
    BASE_DIR, OUTPUT_DIR, OUTRO_VIDEO_PATH, OUTRO_ASSET_NAME
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

def main():
    print("\n" + "="*60)
    print("   RESUMING SHERU PIPELINE FROM CLIP 2 (NO RE-PROMPTING)")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        
        # 1. Get Clip 2 Prompt from ChatGPT tab
        print("\n[1/3] Extracting Clip 2 prompt from current ChatGPT tab...")
        chatgpt_page = [pg for pg in context.pages if "chatgpt.com" in pg.url][0]
        codes = [c.inner_text().strip() for c in chatgpt_page.locator("code").all() if len(c.inner_text().strip()) > 100]
        if len(codes) < 2:
            raise RuntimeError("Could not find Clip 2 in ChatGPT code blocks.")
        clip2_raw = codes[-1]
        
        # Strip header like "Clip 2 (0:10–0:20)"
        if "Clip 2" in clip2_raw:
            clip2_prompt = clip2_raw.split("Clip 2")[-1]
            if "(" in clip2_prompt and ")" in clip2_prompt:
                clip2_prompt = clip2_prompt.split(")")[-1].strip()
        else:
            clip2_prompt = clip2_raw.strip()
            
        print(f"  [✓] Clip 2 prompt loaded ({len(clip2_prompt)} characters)!")
        print(f"      Preview: {clip2_prompt[:120]}...\n")
        
        # 2. Open Google Flow Tab
        print("[2/3] Connecting to Google Flow Scene...")
        flow_page = [pg for pg in context.pages if "flow.google.com" in pg.url][0]
        flow_page.bring_to_front()
        time.sleep(1)
        
        # Check if already in timeline editor or need to double-click tile
        plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
        if not (plus_btn.count() > 0 and plus_btn.is_visible()):
            print("  [*] Entering timeline editor from canvas via double-click...")
            tile = flow_page.locator('flow-video-tile, img.thumbnail').first
            tile.wait_for(state="visible", timeout=15000)
            tile.dblclick()
            time.sleep(3)
            
        print("  [✓] Timeline editor active!")
        
        def approve_credits():
            try:
                btn = flow_page.locator('button:has-text("Always approve in project"), button:has-text("Approve")').first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    print("  [✓] Credit approval confirmed!")
                    time.sleep(1)
            except Exception:
                pass

        def wait_for_render(label: str):
            print(f"  [*] Rendering {label} (1-3 minutes)...")
            start = time.time()
            time.sleep(10)
            while time.time() - start < 360:
                approve_credits()
                elapsed = int(time.time() - start)
                
                plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
                is_timeline_done = plus_btn.count() > 0 and plus_btn.is_visible()
                
                spinners = flow_page.locator('[role="progressbar"], .loading-spinner, :has-text("Generating...")')
                is_spinning = spinners.count() > 0 and spinners.first.is_visible()
                
                if is_timeline_done and not is_spinning and elapsed > 15:
                    print(f"\n  [✓] {label} finished rendering in {elapsed}s!")
                    time.sleep(2)
                    return
                    
                print(f"    ... {label} progress: {elapsed}s elapsed ...", end="\r")
                time.sleep(5)
                
        # 3. Extend with Clip 2
        print("\n[3/3] Extending timeline with Clip 2 (10s slider)...")
        extend_opt = flow_page.locator('[role="menuitem"]:has-text("Extend"), button:has-text("Extend")').first
        if not (extend_opt.count() > 0 and extend_opt.is_visible()):
            plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
            plus_btn.wait_for(state="visible", timeout=15000)
            plus_btn.click()
            time.sleep(1.5)
            
        extend_opt.wait_for(state="visible", timeout=10000)
        extend_opt.click()
        time.sleep(1.5)
        
        # Adjust slider: 4s -> 10s
        dur_btn = flow_page.locator('button:has-text("4s"), button:has-text("s"):has-text("4")').first
        if dur_btn.count() > 0 and dur_btn.is_visible():
            dur_btn.click()
            time.sleep(0.5)
            
            slider_inp = flow_page.locator('input.mdc-slider__input, input[aria-label="Extend Length"]').first
            if slider_inp.count() > 0:
                slider_inp.fill("10")
                slider_inp.dispatch_event("input")
                slider_inp.dispatch_event("change")
                time.sleep(0.5)
                
            dur_10_btn = flow_page.locator('button:has-text("10s")').first
            if dur_10_btn.count() > 0 and dur_10_btn.is_visible():
                dur_10_btn.click()
            else:
                flow_page.keyboard.press("Escape")
            time.sleep(0.5)
            
        # Paste Clip 2
        prompt_box = flow_page.locator('div.ProseMirror, div[aria-label="What happens next?"], div[aria-label="Describe your goal"]').first
        prompt_box.click(force=True)
        prompt_box.fill(clip2_prompt)
        time.sleep(1)
        
        gen_btn = flow_page.locator('button[aria-label="Start generation"]').first
        gen_btn.click()
        wait_for_render("Clip 2 (10s Extension)")
        
        # 4. Attach Outro Clip (1122)
        print(f"\n  [*] Attaching outro clip ('{OUTRO_ASSET_NAME}') to Flow timeline...")
        flow_page.keyboard.press("Escape")
        time.sleep(1)
        
        plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
        plus_btn.wait_for(state="visible", timeout=15000)
        plus_btn.click()
        time.sleep(1.5)
        
        add_clip_item = flow_page.locator('[role="menuitem"]:has-text("Add clip"), button:has-text("Add clip")').first
        add_clip_item.wait_for(state="visible", timeout=10000)
        add_clip_item.click()
        time.sleep(2)
        
        # Select outro item (1122)
        items = flow_page.locator(f':has-text("{OUTRO_ASSET_NAME}")').all()
        for item in items:
            if item.is_visible():
                item.click()
                break
        time.sleep(1)
        
        add_media_btn = flow_page.locator('button:has-text("Add media")').first
        add_media_btn.wait_for(state="visible", timeout=15000)
        for _ in range(30):
            if not add_media_btn.is_disabled():
                add_media_btn.click()
                print("  [✓] Outro clip attached to Flow timeline!")
                break
            time.sleep(1)
        time.sleep(3)
        
        # 5. Download Scene
        print("\n  [*] Downloading complete scene from Google Flow...")
        downloads_dir = Path.home() / "Downloads"
        before_files = set(downloads_dir.glob("*.*"))
        
        dl_btn = flow_page.locator('button[aria-label="Download scene"], button:has-text("download")').first
        dl_btn.wait_for(state="visible", timeout=15000)
        dl_btn.click(force=True)
        print("  [*] Clicked 'Download scene' button in Google Flow...")
        
        new_file = None
        start = time.time()
        while time.time() - start < 60:
            after_files = set(downloads_dir.glob("*.*"))
            diff = [f for f in (after_files - before_files) if f.suffix.lower() in [".mp4", ".zip"]]
            crdownloads = list(downloads_dir.glob("*.crdownload"))
            if diff and not crdownloads:
                new_file = diff[0]
                time.sleep(2)
                break
            time.sleep(1)
            
        output_final = OUTPUT_DIR / "sheru_final_complete.mp4"
        
        if new_file and new_file.suffix.lower() == ".mp4":
            print(f"  [✓] Downloaded direct complete video: {new_file.name}")
            shutil.copy2(new_file, output_final)
        elif new_file and new_file.suffix.lower() == ".zip":
            print(f"  [✓] Downloaded scene zip: {new_file.name}. Extracting...")
            temp_dir = OUTPUT_DIR / "temp_extract"
            temp_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(new_file, 'r') as z:
                z.extractall(temp_dir)
            mp4s = list(temp_dir.glob("*.mp4"))
            longest_mp4 = max(mp4s, key=lambda f: f.stat().st_size)
            shutil.copy2(longest_mp4, output_final)
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            recent_mp4s = sorted(downloads_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if recent_mp4s:
                shutil.copy2(recent_mp4s[0], output_final)
                
        print("\n" + "="*60)
        print(f"  [🎉 SUCCESS 🎉] Complete video generated and saved:")
        print(f"  --> {output_final}")
        print(f"  --> Total size: {output_final.stat().st_size / (1024*1024):.2f} MB")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
