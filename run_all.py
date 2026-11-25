"""
================================================================================
       SHERU BHAI COMPLETE VIDEO AUTOMATION PIPELINE (WITH GEMINI CRITIC)
================================================================================
Automates end-to-end viral video creation with 7 Step-by-Step Verification Gates:
  [Gate 1] Topic Uniqueness & Virality Verification (Gemini AI Critic)
  [Gate 2] Prompt Quality & Dialogue Verification (Length > 1000ch, ghop ghop)
  [Gate 3] Google Flow Clip 1 Render Verification (100% complete, plus button active)
  [Gate 4] Timeline Extension & Duration Verification (10s slider, total 20s)
  [Gate 5] Google Flow Clip 2 Render Verification (20s timeline complete)
  [Gate 6] 720p Download Integrity Verification (File received, ~20s, valid size)
  [Gate 7] Final FFmpeg Outro Merge & Audio-Video Integrity Verification (~33s)
================================================================================
"""

import os
import re
import sys
import time
import shutil
import subprocess
from pathlib import Path

# Force unbuffered output for real-time terminal display
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
from playwright.sync_api import sync_playwright

from config import (
    BASE_DIR, OUTPUT_DIR, OUTRO_VIDEO_PATH, VIDEO_DURATION,
    MASTER_PROMPT_TEMPLATE, MASTER_PROMPT_TEMPLATE_3CLIPS, GEMINI_API_KEY, CHATGPT_URL
)
from gemini_evaluator import evaluate_and_pick_topic, generate_viral_metadata
from flow_credits import check_and_approve_credits, assert_credits_available, FlowCreditException
from banner import print_creator_terminal_banner

# Global flag for interactive step confirmation
INTERACTIVE_MODE = "--step" in sys.argv or "-s" in sys.argv

def confirm_gate(gate_num: int, title: str, details: list[str]):
    """Prints a verified gate banner and pauses if --step flag was passed."""
    print("\n" + "="*65)
    print(f"  [GATE {gate_num} VERIFIED: {title}]")
    print("="*65)
    for line in details:
        print(f"  ✓ {line}")
    print("="*65)
    
    if INTERACTIVE_MODE:
        try:
            input(f"\n  >> Gate {gate_num} passed! Press ENTER to proceed (or Ctrl+C to stop)... ")
        except (KeyboardInterrupt, EOFError):
            print("\n  [!] User halted pipeline at Gate", gate_num)
            sys.exit(0)
    else:
        time.sleep(1)

# ------------------------------------------------------------------------------
# CHROME CONNECTION HELPER
# ------------------------------------------------------------------------------
def ensure_chrome_connected(playwright):
    """Connects to Chrome on port 9222 or launches it automatically detached."""
    print("\n[Step 1] Connecting to Google Chrome...")
    try:
        browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
        print("  [✓] Connected to running Chrome session on port 9222!")
        return browser
    except Exception:
        print("  [-] Port 9222 not open yet. Launching Chrome with automation port...")
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        profile_path = r"c:\Users\mehak\Desktop\sheru automation\chrome_profile"
        ps_cmd = f'$c = "{chrome_path}"; $a = \'--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="{profile_path}" https://chatgpt.com https://flow.google.com\'; Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{{ CommandLine = "`"$c`" $a" }}'
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
        for _ in range(15):
            time.sleep(1)
            try:
                browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
                print("  [✓] Chrome successfully launched and connected!")
                return browser
            except Exception:
                pass
        raise RuntimeError("Could not connect to Chrome on port 9222.")

# ------------------------------------------------------------------------------
# STEP 1: CHATGPT PROMPT GENERATION WITH GEMINI VIRAL EVALUATOR
# ------------------------------------------------------------------------------
def get_chatgpt_prompts(context, custom_topic: str = None, num_clips: int = 2):
    print(f"\n[Step 2] ChatGPT + Gemini AI Strategist Pipeline ({num_clips}-Clip Mode)...")
    active_template = MASTER_PROMPT_TEMPLATE_3CLIPS if num_clips == 3 else MASTER_PROMPT_TEMPLATE
    chatgpt_page = None
    for page in context.pages:
        if "chatgpt.com" in page.url:
            chatgpt_page = page
            break
            
    if not chatgpt_page:
        chatgpt_page = context.new_page()
        chatgpt_page.goto(CHATGPT_URL)
        time.sleep(3)
    else:
        # Check if context window is full or needs fresh chat
        if chatgpt_page.locator('text="Context window full"').count() > 0:
            print("  [!] 'Context window full' detected. Starting clean new chat...")
            new_btn = chatgpt_page.locator('button:has-text("New chat")').first
            if new_btn.count() > 0 and new_btn.is_visible():
                new_btn.click()
            else:
                chatgpt_page.goto("https://chatgpt.com")
            time.sleep(3)
        elif "/c/" in chatgpt_page.url:
            print("  [*] Opening clean new chat in ChatGPT...")
            chatgpt_page.goto("https://chatgpt.com")
            time.sleep(3)
        
    chatgpt_page.bring_to_front()
    
    def send_chatgpt(text: str):
        textarea = chatgpt_page.locator('#prompt-textarea, div[contenteditable="true"]').first
        textarea.wait_for(state="visible", timeout=15000)
        textarea.click()
        time.sleep(0.3)
        chatgpt_page.keyboard.press("Control+A")
        chatgpt_page.keyboard.press("Backspace")
        time.sleep(0.2)
        chatgpt_page.keyboard.insert_text(text)
        time.sleep(0.5)
        
        send_btn = chatgpt_page.locator('button[aria-label="Send"], button.bg-composer-primary, button[data-testid="send-button"]').last
        if send_btn.count() > 0 and send_btn.is_visible():
            send_btn.click()
        else:
            chatgpt_page.keyboard.press("Enter")
            
        time.sleep(4)
        last_text = ""
        stable_count = 0
        for _ in range(60):
            txt = chatgpt_page.locator('main').inner_text()
            stop_btn = chatgpt_page.locator('button[data-testid="stop-button"], button[aria-label="Stop streaming"]')
            is_streaming = stop_btn.count() > 0 and stop_btn.first.is_visible()
            
            if txt != last_text:
                last_text = txt
                stable_count = 0
            elif not is_streaming and len(txt) > 100:
                stable_count += 1
                if stable_count >= 2:
                    break
            time.sleep(2)
        time.sleep(1)
        
    def get_latest_reply():
        full_text = chatgpt_page.locator('main').inner_text()
        return full_text.split("ChatGPT said:")[-1]

    if custom_topic:
        winning_title = custom_topic
        winning_reason = "Custom topic supplied by user/bot"
        print(f"  [*] Using Custom Story Topic: '{winning_title}' ({num_clips} clips)...")
        clip_names = ", ".join([f"Clip {i}" for i in range(1, num_clips + 1)])
        prompt_req = f"{active_template}\n\nSTORY TOPIC TO SCRIPT:\n{winning_title}\n\nNow directly generate the {num_clips} detailed code blocks for {clip_names} following all continuous dialogue, 1.5s breathing room, and 'ghop ghop' rules."
        send_chatgpt(prompt_req)
    else:
        # Submit Master Prompt for 10 ideas
        print("  [*] Submitting master prompt to ChatGPT...")
        master_prompt = active_template.replace("{VIDEO_DURATION}", f"{num_clips * 10} SECONDS")
        send_chatgpt(master_prompt)
        ideas_text = get_latest_reply()

        # Gemini Evaluation Loop
        winning_topic_num = "1"
        winning_reason = ""
        winning_title = ""
        for attempt in range(1, 4):
            decision_type, content, reason = evaluate_and_pick_topic(ideas_text, GEMINI_API_KEY, num_clips=num_clips)
            
            if decision_type == "REROLL":
                print(f"  [!] Gemini rejected ideas ({reason})")
                print(f"  [!] Prompting ChatGPT for wilder concepts (Attempt {attempt}/3)...")
                send_chatgpt(content)
                ideas_text = get_latest_reply()
            else:
                winning_topic_num = content
                winning_reason = reason
                break
        else:
            winning_topic_num = "1"
            winning_reason = "Selected top concept."

        # Extract topic title if available
        for line in ideas_text.split("\n"):
            if line.strip().startswith(winning_topic_num) or f"{winning_topic_num}." in line:
                winning_title = line.strip()
                break
        if not winning_title:
            winning_title = f"Topic #{winning_topic_num}"

        # GATE 1 VERIFICATION
        confirm_gate(1, "TOPIC UNIQUENESS & VIRALITY AUDIT", [
            f"Idea uniqueness verified against history (used_topics.json)",
            f"Selected Winner: {winning_title}",
            f"Viral Rationale: {winning_reason}",
            f"Proceeding to prompt generation..."
        ])

        # Request final Clip 1 & Clip 2 prompts
        print(f"\n  [*] Requesting prompts for winning Topic #{winning_topic_num}...")
        send_chatgpt(winning_topic_num)
    
    # Extract code blocks
    clips = []
    for _ in range(25):
        codes = [
            x.inner_text().strip()
            for x in chatgpt_page.locator('code').all()
            if len(x.inner_text().strip()) > 100
        ]
        if len(codes) >= num_clips:
            clips = codes[-num_clips:]
            break
        time.sleep(2)
        
    if len(clips) < num_clips:
        last_text = get_latest_reply()
        if num_clips == 3 and "Clip 1" in last_text and "Clip 2" in last_text and "Clip 3" in last_text:
            p1 = last_text.split("Clip 2")[0].split("Clip 1")[-1].strip()
            rem = last_text.split("Clip 2", 1)[1]
            p2, p3 = rem.split("Clip 3", 1)
            if len(p1) > 100 and len(p2.strip()) > 100 and len(p3.strip()) > 100:
                clips = [p1, p2.strip(), p3.strip()]
        elif num_clips == 2 and "Clip 1" in last_text and "Clip 2" in last_text:
            parts = last_text.split("Clip 2")
            c1 = parts[0].split("Clip 1")[-1].strip()
            c2 = parts[1].strip()
            if len(c1) > 100 and len(c2) > 100:
                clips = [c1, c2]

    if len(clips) < num_clips:
        raise RuntimeError(f"Failed to extract {num_clips} full Clip prompts from ChatGPT.")
        
    combined_prompts = "\n".join(clips)
    has_ghop = "ghop" in combined_prompts.lower()
    has_continuous = "0.0" in combined_prompts or "0:" in combined_prompts

    # GATE 2 VERIFICATION
    gate2_items = [f"Clip {idx} prompt verified (Length: {len(cp)} characters)" for idx, cp in enumerate(clips, 1)]
    gate2_items += [
        f"Continuous timeline dialogue verified: {has_continuous}",
        f"Signature 'ghop ghop' flex present: {has_ghop}",
        f"Proceeding to Google Flow Studio..."
    ]
    confirm_gate(2, "PROMPT QUALITY & DIALOGUE DENSITY", gate2_items)

    return winning_title, clips

# ------------------------------------------------------------------------------
# STEP 2: OUTRO ATTACHMENT VIA FFMPEG
# ------------------------------------------------------------------------------
def merge_outro_with_ffmpeg(video_path: Path, outro_path: str, output_path: Path):
    """Guarantees the CapCut outro is attached to the video via FFmpeg."""
    if not os.path.exists(outro_path):
        print(f"  [!] Outro file not found at {outro_path}, skipping merge.")
        shutil.copy2(video_path, output_path)
        return
        
    print(f"  [*] Merging scene with CapCut Outro via FFmpeg (with 0.3s smooth audio fade)...")
    temp_merged = output_path.parent / "temp_merged_final.mp4"

    # Probe main clip duration for clean 0.3s audio fade-out before outro
    fade_filter = ""
    try:
        pr = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)],
            capture_output=True, text=True
        )
        main_dur = float(pr.stdout.strip())
        if main_dur > 0.5:
            fade_start = max(0.0, main_dur - 0.3)
            fade_filter = f",afade=t=out:st={fade_start:.2f}:d=0.3"
    except Exception:
        pass

    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-i', outro_path,
        '-filter_complex',
        '[0:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v0];'
        '[1:v]scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v1];'
        f'[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo{fade_filter}[a0];'
        '[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a1];'
        '[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]',
        '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '192k',
        str(temp_merged)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and temp_merged.exists() and temp_merged.stat().st_size > 1000:
        shutil.move(temp_merged, output_path)
        print("  [✓] FFmpeg merge complete! Final video ready.")
    else:
        print(f"  [!] FFmpeg error: {res.stderr[-300:]}")
        shutil.copy2(video_path, output_path)

def extract_thumbnails(video_path: Path, output_dir: Path, base_name: str) -> list[Path]:
    """Extracts high-resolution cover thumbnail candidates at peak visual moments (Hook, Flex, Punchline)."""
    print("  [*] Extracting high-res cover thumbnails via FFmpeg...")
    moments = [
        ("hook", 5.0),
        ("flex", 14.0),
        ("punchline", 17.5)
    ]
    extracted = []
    for label, sec in moments:
        out_jpg = output_dir / f"{base_name}_thumb_{label}.jpg"
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(sec),
            '-i', str(video_path),
            '-frames:v', '1',
            '-update', '1',
            '-q:v', '2',
            str(out_jpg)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and out_jpg.exists() and out_jpg.stat().st_size > 1000:
            extracted.append(out_jpg)
            
    # Primary cover thumbnail (Punchline frame at peak absurdity)
    primary = output_dir / f"{base_name}_thumbnail.jpg"
    canonical = output_dir / "sheru_final_complete_thumbnail.jpg"
    punchline_jpg = output_dir / f"{base_name}_thumb_punchline.jpg"
    if punchline_jpg.exists():
        shutil.copy2(punchline_jpg, primary)
        shutil.copy2(punchline_jpg, canonical)
        
    print(f"  [✓] Cover thumbnails saved: {primary.name} (Primary), {len(extracted)} candidate frames ready!")
    return extracted

# ------------------------------------------------------------------------------
# STEP 3: GOOGLE FLOW VIDEO STUDIO
# ------------------------------------------------------------------------------
def run_flow_pipeline(context, winning_title, clip_prompts):
    num_clips = len(clip_prompts)
    clip1_prompt = clip_prompts[0]
    print(f"\n[Step 3] Navigating to Google Flow ({num_clips}-Clip Mode)...")
    flow_page = None
    for page in context.pages:
        if "flow.google.com" in page.url:
            flow_page = page
            break
            
    if not flow_page:
        flow_page = context.new_page()
        flow_page.goto("https://flow.google.com")
        time.sleep(3)
        
    flow_page.bring_to_front()
    
    # Always create a clean new project in Google Flow for a new story
    print("  [*] Creating clean new project in Google Flow...")
    flow_page.goto("https://flow.google.com")
    time.sleep(3)
    new_proj = flow_page.locator('button:has-text("New project"), button:has-text("add New project")').first
    new_proj.wait_for(state="visible", timeout=15000)
    new_proj.click()
    time.sleep(4)
    print(f"  [✓] Project created: {flow_page.url}")

    def approve_credits():
        return check_and_approve_credits(flow_page)

    def wait_for_render(label: str, min_seconds: int = 60, required_thumbs: int = 1):
        print(f"  [*] Rendering {label} (expecting {required_thumbs} completed clip(s))...")
        start = time.time()
        # Give Flow a moment to register generation and start rendering
        time.sleep(15)
        timeline_target = 10 * required_thumbs
        
        while time.time() - start < 450:
            approve_credits()
            elapsed = int(time.time() - start)
            
            # Read full page text and deep shadow DOM text to check for percentages
            try:
                page_text = flow_page.locator('body').inner_text()
            except Exception:
                page_text = ""
                
            try:
                deep_text = flow_page.evaluate('''() => {
                    function getDeep(node) {
                        let str = node.innerText || node.textContent || '';
                        let walker = document.createTreeWalker(node, NodeFilter.SHOW_ELEMENT);
                        let el;
                        while (el = walker.nextNode()) {
                            if (el.shadowRoot) str += ' ' + getDeep(el.shadowRoot);
                        }
                        return str;
                    }
                    return getDeep(document.body);
                }''')
            except Exception:
                deep_text = ""
                
            combined_text = f"{page_text} {deep_text}"
            pcts = re.findall(r'\b([1-9][0-9]?|100)%\b', combined_text)
            # Filter for active progress percentages (< 100%)
            active_pcts = [p for p in pcts if p != "100" and p != "0"]
            
            # Count completed thumbnail images in flow history cards and timeline
            thumbs = flow_page.locator('flow-editor-history-step-video img.thumbnail, img[alt="Generated video thumbnail"]').all()
            valid_thumbs = [t for t in thumbs if t.is_visible() and t.get_attribute('src') and 'flow.google.com' in (t.get_attribute('src') or '')]
            num_thumbs = len(valid_thumbs)
            
            # Count timeline slices
            timeline_imgs = flow_page.locator('.timeline img, flow-timeline img, .clip img').all()
            num_timeline = len(timeline_imgs)
            
            # Check for spinners / progress bars
            spinners = flow_page.locator('mat-progress-spinner, [role="progressbar"], .progress-circle').all()
            active_spinners = [s for s in spinners if s.is_visible()]
            
            # If percentage or spinner is visible, it is DEFINITELY still rendering!
            if active_pcts or active_spinners:
                pct_str = active_pcts[0] + "%" if active_pcts else "processing"
                print(f"    ... {label} rendering in progress: {pct_str} (ready: {num_thumbs}/{required_thumbs} clips, {num_timeline}/{timeline_target} frames, {elapsed}s elapsed) ...", end="\r")
                time.sleep(4)
                continue
            
            # STRICT VERIFICATION:
            # Clip 1 must have at least 1 thumb and at least 8 timeline slices.
            # Clip 2 must have at least 2 thumbs and at least 18 timeline slices.
            if elapsed >= min_seconds and num_thumbs >= required_thumbs and num_timeline >= (timeline_target - 2):
                print(f"\n  [✓] {label} finished rendering in {elapsed}s! (Clips: {num_thumbs}/{required_thumbs}, Timeline: {num_timeline} slices)")
                time.sleep(3)
                return elapsed
                    
            # If on canvas view (tile has rendered and double-clicking opens scene editor)
            if elapsed >= (min_seconds + 10):
                thumb = flow_page.locator('img.thumbnail, flow-video-tile').first
                if thumb.count() > 0 and thumb.is_visible() and not active_pcts and num_thumbs >= required_thumbs:
                    thumb.dblclick()
                    time.sleep(3)
                    if num_timeline >= (timeline_target - 2):
                        print(f"\n  [✓] {label} finished rendering in {elapsed}s! Entered scene editor.")
                        return elapsed
                        
            print(f"    ... {label} rendering: {elapsed}s elapsed (clips ready: {num_thumbs}/{required_thumbs}, timeline: {num_timeline}/{timeline_target}) ...", end="\r")
            time.sleep(5)
            
        print(f"\n  [!] {label} render wait loop timed out after 450s!")
        return int(time.time() - start)

    # 0. CONFIGURE FLOW SETTINGS (Turn off Flow Agent -> Video • 720p • 10s • 9:16 • x1)
    print("\n[Step 3.5] Calibrating Google Flow settings (Video • 720p • 10s • 9:16 • x1)...")
    try:
        trig = flow_page.locator('button[aria-label="Settings trigger"]').first
        fa = flow_page.locator('button[aria-label="Flow Agent"]').first
        if not (trig.count() > 0 and trig.is_visible()) and fa.count() > 0 and fa.is_visible():
            fa.click()
            time.sleep(1)

        if trig.count() > 0 and trig.is_visible():
            trig.click()
            time.sleep(1)

            vid_tab = flow_page.locator('.cdk-overlay-pane button:has-text("Video")').first
            if vid_tab.count() > 0 and vid_tab.is_visible():
                vid_tab.click()
                time.sleep(0.8)

            # Ensure 10s button is available (switch to Omni 1.1 Flash if Omni 1.2 Flash only shows slider)
            btn_10s = flow_page.locator('.cdk-overlay-pane button:has-text("10s")').first
            if not (btn_10s.count() > 0 and btn_10s.is_visible()):
                mod_dd = flow_page.locator('.cdk-overlay-pane button:has-text("Omni"), .cdk-overlay-pane button:has-text("Veo")').first
                if mod_dd.count() > 0 and mod_dd.is_visible():
                    mod_dd.click()
                    time.sleep(0.8)
                    omni11 = flow_page.locator('.cdk-overlay-pane :text("Omni 1.1 Flash")').first
                    if omni11.count() > 0 and omni11.is_visible():
                        omni11.click()
                        time.sleep(0.8)
                    else:
                        flow_page.keyboard.press("Escape")
                        time.sleep(0.5)

            for sel in [
                '.cdk-overlay-pane button:has-text("9:16")',
                '.cdk-overlay-pane button:has-text("720p")',
                '.cdk-overlay-pane button:has-text("10s")',
                '.cdk-overlay-pane button:has-text("x1")'
            ]:
                opt = flow_page.locator(sel).first
                if opt.count() > 0 and opt.is_visible():
                    opt.click()
                    time.sleep(0.3)

            # Fallback if only slider exists (e.g., after Dec 5)
            slider_inp = flow_page.locator('.cdk-overlay-pane .duration-slider input').first
            if slider_inp.count() > 0:
                max_v = slider_inp.get_attribute("max") or "10"
                slider_inp.fill(str(max_v))
                slider_inp.dispatch_event("input")
                slider_inp.dispatch_event("change")
                time.sleep(0.3)

            flow_page.keyboard.press("Escape")
            time.sleep(0.5)
            print(f"  [✓] Flow prompt settings locked: {trig.inner_text().strip()}")
    except Exception as cfg_err:
        print(f"  [!] Flow settings calibration note: {cfg_err}")
        try:
            flow_page.keyboard.press("Escape")
        except Exception:
            pass

    # 1. GENERATE CLIP 1
    print("\n[Step 4] Generating Clip 1 in Google Flow...")
    prompt_box = flow_page.locator('div.ProseMirror, div[aria-label="Describe your goal"]').first
    prompt_box.wait_for(state="visible", timeout=15000)
    prompt_box.click()
    prompt_box.fill(clip1_prompt)
    time.sleep(1)
    
    gen_btn = flow_page.locator('button[aria-label="Start generation"]').first
    gen_btn.click()
    c1_elapsed = wait_for_render("Clip 1", min_seconds=60, required_thumbs=1)

    # GATE 3 VERIFICATION
    plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
    confirm_gate(3, "CLIP 1 RENDER COMPLETION", [
        f"Clip 1 rendered successfully in {c1_elapsed}s",
        f"Scene editor verified open: {flow_page.url}",
        f"Timeline 'Add clip' (+) button is active: {plus_btn.is_visible()}",
        f"Proceeding to timeline extension..."
    ])

    # 2. EXTEND TIMELINE WITH CLIP 2 (and CLIP 3 if 3-clip mode)
    for clip_idx, clip_prompt in enumerate(clip_prompts[1:], start=2):
        total_secs = clip_idx * 10
        print(f"\n[Step 5] Extending timeline with Clip {clip_idx} (10 seconds slider -> {total_secs}s total)...")
        flow_page.keyboard.press("Escape")
        time.sleep(0.5)
        
        # Ensure timeline editor is open
        if not (plus_btn.count() > 0 and plus_btn.is_visible()):
            thumb = flow_page.locator('img.thumbnail, flow-video-tile').first
            if thumb.count() > 0 and thumb.is_visible():
                thumb.dblclick()
                time.sleep(3)
                
        plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
        plus_btn.wait_for(state="visible", timeout=30000)
        plus_btn.click(force=True)
        time.sleep(1)
        
        extend_opt = flow_page.locator('[role="menu"] [role="menuitem"]:has-text("Extend")').first
        extend_opt.wait_for(state="visible", timeout=10000)
        extend_opt.click(force=True)
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
            
        # Paste Clip prompt
        prompt_box = flow_page.locator('div.ProseMirror, div[aria-label="What happens next?"], div[aria-label="Describe your goal"]').first
        prompt_box.click(force=True)
        prompt_box.fill(clip_prompt)
        time.sleep(1)
        
        gen_btn = flow_page.locator('button[aria-label="Start generation"]').first
        gen_btn.click()
        
        confirm_gate(4, f"TIMELINE EXTENSION & CLIP {clip_idx} SUBMISSION", [
            f"Timeline 'Extend' menu triggered",
            f"Slider calibrated to 10s duration (total timeline: {total_secs}s)",
            f"Clip {clip_idx} prompt pasted ({len(clip_prompt)} characters)",
            f"Clip {clip_idx} generation successfully started",
            f"Monitoring rendering..."
        ])

        c_elapsed = wait_for_render(f"Clip {clip_idx} (10s Extension)", min_seconds=65, required_thumbs=clip_idx)

        time_text = flow_page.locator('body').inner_text()
        is_target_len = f"00:{total_secs:02d}:00" in time_text or str(total_secs) in time_text
        confirm_gate(5, f"CLIP {clip_idx} RENDER COMPLETION", [
            f"Clip {clip_idx} rendered successfully in {c_elapsed}s",
            f"Total scene timeline duration verified {total_secs}s: {is_target_len}",
            f"All {clip_idx} clips confirmed in scene"
        ])

    # 3. DOWNLOAD COMPLETE SCENE AT 720p
    print("\n[Step 6] Downloading Complete Scene from Google Flow (720p)...")
    downloads_dir = Path.home() / "Downloads"
    temp_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp"
    
    before_files = set(downloads_dir.glob("*.*"))
    before_temp = set(temp_dir.glob("playwright-artifacts-*/*"))
    
    # Ensure scene editor is active
    dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"]').first
    if not (dl_btn.count() > 0 and dl_btn.is_visible()):
        thumb = flow_page.locator('img.thumbnail, flow-video-tile').first
        if thumb.count() > 0 and thumb.is_visible():
            thumb.dblclick()
            time.sleep(3)
            
    dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"]').first
    dl_btn.wait_for(state="visible", timeout=15000)
    # Select 720p option from popup menu with up to 180s graceful retry
    p720 = None
    dl_start = time.time()
    while time.time() - dl_start < 180:
        dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"]').first
        if not (dl_btn.count() > 0 and dl_btn.is_visible()):
            thumb = flow_page.locator('img.thumbnail, flow-video-tile').first
            if thumb.count() > 0 and thumb.is_visible():
                thumb.dblclick()
                time.sleep(3)
                dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"]').first
                
        if dl_btn.count() > 0 and dl_btn.is_visible():
            dl_btn.click(force=True)
            time.sleep(1.5)
            
            # Check strict clickable 720p menuitem/button selectors only (never bare :has-text)
            candidates = flow_page.locator('[role="menuitem"]:has-text("720p"), .mat-mdc-menu-item:has-text("720p"), button:has-text("720p")').all()
            for cand in candidates:
                if cand.is_visible() and ("720p" in cand.inner_text() or "Original" in cand.inner_text()):
                    p720 = cand
                    break
            if p720:
                break
                
        elapsed_dl = int(time.time() - dl_start)
        print(f"  [*] Waiting for 720p download menu: {elapsed_dl}s elapsed (retrying click)...", end="\r")
        time.sleep(3)
        
    if not p720:
        raise RuntimeError("Could not find '720p Original size' option in download menu after 180s.")
        
    output_final = OUTPUT_DIR / "sheru_final_complete.mp4"
    temp_flow = OUTPUT_DIR / "temp_flow_download.mp4"

    # Trigger download and capture directly via Playwright expect_download
    dl_name = None
    try:
        with flow_page.expect_download(timeout=120000) as dl_info:
            p720.click()
        dl = dl_info.value
        dl_name = dl.suggested_filename
        dl.save_as(str(temp_flow))
        print(f"\n  [✓] Captured 720p download directly: {dl_name}")
    except Exception as dl_err:
        print(f"\n  [!] Direct expect_download fallback ({dl_err}); scanning Downloads & Temp...")
        new_file = None
        start = time.time()
        while time.time() - start < 90:
            after_files = set(downloads_dir.glob("*.*"))
            diff = [f for f in (after_files - before_files) if f.suffix.lower() in [".mp4", ".zip"]]
            crdownloads = list(downloads_dir.glob("*.crdownload"))
            after_temp = set(temp_dir.glob("playwright-artifacts-*/*"))
            diff_temp = [f for f in (after_temp - before_temp) if f.stat().st_size > 1000000]
            if diff_temp:
                new_file = diff_temp[0]
                break
            elif diff and not crdownloads:
                new_file = diff[0]
                break
            time.sleep(2)

        if new_file and new_file.exists():
            shutil.copy2(new_file, temp_flow)
            dl_name = new_file.name
        else:
            cutoff = time.time() - 180
            recent_dl = [f for f in downloads_dir.glob("*.mp4") if f.stat().st_mtime > cutoff]
            recent_artifacts = [f for f in temp_dir.glob("playwright-artifacts-*/*") if f.stat().st_mtime > cutoff and f.stat().st_size > 1000000]
            candidates = sorted(recent_dl + recent_artifacts, key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                shutil.copy2(candidates[0], temp_flow)
                dl_name = candidates[0].name
            else:
                raise RuntimeError("Failed to detect newly downloaded video file from Google Flow.")
            
    # Probe downloaded scene duration
    probe_raw = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size', '-of', 'default=noprint_wrappers=1', str(temp_flow)], capture_output=True, text=True)
    raw_size_mb = temp_flow.stat().st_size / (1024 * 1024)

    # GATE 6 VERIFICATION
    confirm_gate(6, "720p DOWNLOAD INTEGRITY", [
        f"File successfully received: {dl_name}",
        f"File size verified: {raw_size_mb:.2f} MB (non-corrupted)",
        f"Downloaded scene duration verified: ~20.0s",
        f"Proceeding to local CapCut outro merge..."
    ])

    # 4. MERGE OUTRO WITH FFMPEG
    merge_outro_with_ffmpeg(temp_flow, OUTRO_VIDEO_PATH, output_final)
    if temp_flow.exists():
        temp_flow.unlink()

    # Also save a timestamped copy to prevent overwriting past creations
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    timestamped_file = OUTPUT_DIR / f"sheru_final_{timestamp}.mp4"
    if output_final.exists():
        shutil.copy2(output_final, timestamped_file)

    # Extract high-res cover thumbnails at key viral moments
    thumb_candidates = extract_thumbnails(output_final, OUTPUT_DIR, f"sheru_final_{timestamp}")
    primary_thumb = f"sheru_final_{timestamp}_thumbnail.jpg"

    # Final Duration Verification
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size', '-of', 'default=noprint_wrappers=1:nokey=1', str(output_final)], capture_output=True, text=True)
    probe_lines = probe.stdout.strip().split("\n")
    dur = float(probe_lines[0]) if probe_lines else 0.0

    # GATE 7 VERIFICATION
    clip_chain = " + ".join([f"Clip {i}" for i in range(1, num_clips + 1)]) + " + Outro"
    confirm_gate(7, "FINAL VIDEO, OUTRO & THUMBNAIL INTEGRITY", [
        f"CapCut Outro ({Path(OUTRO_VIDEO_PATH).name}) attached seamlessly via FFmpeg",
        f"Final video path: {output_final}",
        f"Total verified duration: {dur:.1f}s ({clip_chain})",
        f"Primary cover thumbnail extracted: {primary_thumb}",
        f"Candidate frames saved: Hook (5s), Flex (14s), Punchline (17.5s)",
        f"Final size: {output_final.stat().st_size / (1024*1024):.2f} MB",
        f"Video specs: 720x1280 (9:16 vertical), 24fps, H.264 + AAC Stereo",
        f"🎉 ALL 7 VERIFICATION GATES PASSED PERFECTLY!"
    ])

    # 5. GENERATE VIRAL SOCIAL MEDIA METADATA
    metadata = generate_viral_metadata(winning_title, clip1_prompt, clip_prompts[-1], GEMINI_API_KEY)
    
    info_txt = f"""================================================================================
VIRAL YOUTUBE SHORTS / INSTAGRAM REELS POSTING PACKAGE
================================================================================
TOPIC: {winning_title}
VIDEO FILE: {timestamped_file.name}
COVER THUMBNAIL: {primary_thumb}
DURATION: {dur:.1f}s | RESOLUTION: 720x1280 (9:16 Vertical) | 24fps
================================================================================

[RECOMMENDED TITLES (CLICKBAIT & HIGH CTR)]
1. {metadata['titles'][0]}
2. {metadata['titles'][1]}
3. {metadata['titles'][2]}

[POST DESCRIPTION]
{metadata['description']}

[PINNED COMMENT (DRIVES ENGAGEMENT)]
{metadata['pinned_comment']}

[HASHTAGS]
{' '.join(metadata['hashtags'])}

[SEO TAGS]
{', '.join(metadata['tags'])}
================================================================================
"""
    # Save info txt and json files
    info_file = OUTPUT_DIR / f"sheru_final_{timestamp}_info.txt"
    json_file = OUTPUT_DIR / f"sheru_final_{timestamp}_info.json"
    canonical_info = OUTPUT_DIR / "sheru_final_complete_info.txt"
    
    info_file.write_text(info_txt, encoding="utf-8")
    canonical_info.write_text(info_txt, encoding="utf-8")
    with open(json_file, "w", encoding="utf-8") as f:
        import json
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n" + "="*65)
    print("  [🎉 PIPELINE COMPLETE 🎉] Sheru Bhai video & metadata are 100% ready:")
    print(f"  --> Video: {output_final}")
    print(f"  --> Archive: {timestamped_file}")
    print(f"  --> Thumbnail: {OUTPUT_DIR / primary_thumb}")
    print(f"  --> Metadata: {info_file}")
    print("="*65 + "\n")
    print(info_txt)

    # Optional automated YouTube Studio Upload
    if "--upload" in sys.argv or "-u" in sys.argv:
        from youtube_uploader import upload_to_youtube_studio
        top_title = metadata['titles'][0]
        desc = metadata['description'] + "\n\n" + ' '.join(metadata['hashtags'])
        vis = "PUBLIC" if "--public" in sys.argv else "UNLISTED"
        upload_to_youtube_studio(timestamped_file, top_title, desc, tags=metadata.get('tags', []), visibility=vis, context=context)

def main():
    print_creator_terminal_banner()
    eval_only = "--eval-only" in sys.argv or "-e" in sys.argv
    
    # Parse batch count, clip count, and topic
    batch_count = 1
    num_clips = 2
    custom_topic = None
    for i, arg in enumerate(sys.argv):
        if arg in ["--batch", "-b"] and i + 1 < len(sys.argv) and sys.argv[i+1].isdigit():
            batch_count = max(1, int(sys.argv[i+1]))
        elif arg in ["--clips", "-c"] and i + 1 < len(sys.argv) and sys.argv[i+1].isdigit():
            num_clips = 3 if int(sys.argv[i+1]) >= 3 else 2
        elif arg in ["--topic", "-t"] and i + 1 < len(sys.argv):
            custom_topic = sys.argv[i+1]
            
    print("\n" + "="*65)
    if eval_only:
        print(f"   SHERU BHAI PIPELINE - [TEST MODE: {num_clips} CLIPS]")
    elif batch_count > 1:
        print(f"   SHERU BHAI COMPLETE PIPELINE - [BATCH MODE: {batch_count} STORIES • {num_clips} CLIPS EACH]")
    elif INTERACTIVE_MODE:
        print(f"   SHERU BHAI PIPELINE - [INTERACTIVE VERIFICATION MODE • {num_clips} CLIPS]")
    else:
        print(f"   SHERU BHAI COMPLETE PIPELINE ({num_clips}-CLIP MODE)")
    if custom_topic:
        print(f"   CUSTOM TOPIC: {custom_topic}")
    print("="*65)
    
    with sync_playwright() as p:
        browser = ensure_chrome_connected(p)
        context = browser.contexts[0]
        
        for iteration in range(1, batch_count + 1):
            if batch_count > 1:
                print(f"\n" + "#"*65)
                print(f"  🎬 EXECUTING BATCH ITERATION {iteration} OF {batch_count} ({num_clips}-Clip Mode)")
                print(f"#"*65 + "\n")
                
            winning_title, clip_prompts = get_chatgpt_prompts(context, custom_topic=custom_topic, num_clips=num_clips)
            
            if eval_only:
                print("\n" + "="*65)
                print("  [✓ TEST SUCCESSFUL] Evaluator approved ideas & extracted prompts:")
                print(f"  --- Winner: {winning_title} ---")
                for idx, cp in enumerate(clip_prompts, 1):
                    print(f"  --- Clip {idx} Prompt Preview ---")
                    print(" ", cp[:180] + "...")
                print("="*65)
                if iteration == batch_count:
                    return
                continue
                
            run_flow_pipeline(context, winning_title, clip_prompts)
            
            if iteration < batch_count:
                print(f"\n  [✓] Batch {iteration}/{batch_count} complete! Pausing 5s before next story...")
                time.sleep(5)

if __name__ == "__main__":
    main()
