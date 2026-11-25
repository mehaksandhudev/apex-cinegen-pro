"""
Google Flow Automation Module
Calibrated end-to-end for Google Flow Studio:
- Project creation / navigation
- Clip 1 prompt & generation
- Timeline '+' -> 'Extend' -> 10s slider configuration -> Clip 2 generation
- Timeline '+' -> 'Add clip' -> Outro media ('1122') -> Add media
- Download scene execution
"""

import time
from pathlib import Path
from playwright.sync_api import Page
from config import OUTRO_VIDEO_PATH, OUTPUT_DIR

class FlowAgent:
    def __init__(self, page: Page):
        self.page = page

    def go_to_flow(self):
        """Navigates to Google Flow."""
        print("[Flow] Navigating to https://flow.google.com...")
        self.page.goto("https://flow.google.com")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)

    def create_new_project(self):
        """Clicks the New Project button if on the home screen."""
        if "flow.google.com/project/" in self.page.url:
            print(f"[Flow] Already in project: {self.page.url}")
            return
            
        print("[Flow] Creating new project...")
        new_proj_btn = self.page.locator('button:has-text("New project"), button:has-text("add New project")').first
        if new_proj_btn.count() > 0 and new_proj_btn.is_visible():
            new_proj_btn.click()
            time.sleep(5)
            print(f"[Flow] New project opened: {self.page.url}")

    def handle_credit_approval(self):
        """Automatically approves credit dialog if it appears."""
        try:
            approve_btn = self.page.locator('button:has-text("Always approve in project"), button:has-text("Approve"), [aria-label*="Approve"]').first
            if approve_btn.count() > 0 and approve_btn.is_visible():
                print("[Flow] Detected credit approval prompt, clicking approve...")
                approve_btn.click()
                time.sleep(1)
        except Exception:
            pass

    def wait_for_video_generation(self, timeout_sec: int = 360):
        """Polls until the video clip finishes generating."""
        print("[Flow] Waiting for video generation to complete (1-3 minutes)...")
        start_time = time.time()
        time.sleep(5)
        
        while time.time() - start_time < timeout_sec:
            self.handle_credit_approval()
            elapsed = int(time.time() - start_time)
            
            # Completion indicators: Add clip (+) button or Redo Extend
            plus_btn = self.page.locator('button[aria-label="Add clip"]').first
            redo_btn = self.page.locator('button:has-text("Redo Extend"), button:has-text("Redo")').first
            
            spinners = self.page.locator('[role="progressbar"], .loading-spinner, :has-text("Generating...")')
            is_generating = spinners.count() > 0 and spinners.first.is_visible()
            
            if (plus_btn.count() > 0 or redo_btn.count() > 0) and not is_generating and elapsed > 20:
                print(f"\n[Flow] Generation completed in {elapsed}s!")
                time.sleep(2)
                return True
                
            print(f"  ... rendering in progress ({elapsed}s elapsed) ...", end="\r")
            time.sleep(5)
            
        print("\n[Flow] Warning: Generation wait timed out.")
        return False

    def generate_clip_1(self, prompt: str):
        """Pastes Clip 1 prompt into the prompt box and hits Start generation."""
        print("\n[Flow] Pasting Clip 1 prompt into prompt box...")
        prompt_box = self.page.locator('div.ProseMirror, div[aria-label="Describe your goal"]').first
        prompt_box.wait_for(state="visible", timeout=15000)
        prompt_box.click()
        prompt_box.fill(prompt)
        time.sleep(1)
        
        gen_btn = self.page.locator('button[aria-label="Start generation"]').first
        gen_btn.wait_for(state="visible", timeout=10000)
        gen_btn.click()
        print("[Flow] Clip 1 generation started!")
        
        self.wait_for_video_generation()

    def set_extend_duration_10s(self):
        """Clicks duration button ('4s'), sets slider to '10s', and closes popup."""
        try:
            dur_btn = self.page.locator('button:has-text("4s"), button:has-text("s"):has-text("4")').first
            if dur_btn.count() > 0 and dur_btn.is_visible():
                print("[Flow] Opening duration slider...")
                dur_btn.click()
                time.sleep(0.5)
                
                # Move slider to 10
                slider_inp = self.page.locator('input.mdc-slider__input, input[aria-label="Extend Length"]').first
                if slider_inp.count() > 0:
                    slider_inp.fill("10")
                    slider_inp.dispatch_event("input")
                    slider_inp.dispatch_event("change")
                    print("[Flow] Slider set to 10s!")
                    time.sleep(0.5)
                    
                # Tap duration button again to close popup
                dur_10_btn = self.page.locator('button:has-text("10s")').first
                if dur_10_btn.count() > 0 and dur_10_btn.is_visible():
                    dur_10_btn.click()
                else:
                    self.page.keyboard.press("Escape")
                time.sleep(0.5)
        except Exception as e:
            print(f"[Flow] Duration config note: {e}")

    def extend_with_clip_2(self, prompt: str):
        """Timeline '+' -> 'Extend' -> sets 10s -> pastes Clip 2 prompt -> triggers extension."""
        print("\n[Flow] Extending timeline with Clip 2 (10 seconds)...")
        
        # 1. Click '+' at the end of the timeline
        plus_btn = self.page.locator('button[aria-label="Add clip"]').first
        plus_btn.wait_for(state="visible", timeout=15000)
        plus_btn.click()
        time.sleep(1)
        
        # 2. Click 'Extend'
        extend_opt = self.page.locator('[role="menuitem"]:has-text("Extend"), button:has-text("Extend")').first
        extend_opt.wait_for(state="visible", timeout=10000)
        extend_opt.click()
        time.sleep(1.5)
        
        # 3. Configure 10s duration
        self.set_extend_duration_10s()
        
        # 4. Paste Clip 2 prompt
        prompt_box = self.page.locator('div.ProseMirror, div[aria-label="What happens next?"], div[aria-label="Describe your goal"]').first
        prompt_box.click(force=True)
        prompt_box.fill(prompt)
        time.sleep(1)
        
        # 5. Start generation
        gen_btn = self.page.locator('button[aria-label="Start generation"]').first
        gen_btn.click()
        print("[Flow] Clip 2 (10s) extension submitted!")
        
        self.wait_for_video_generation()

    def add_outro_clip(self, asset_name: str = "1122"):
        """Timeline '+' -> 'Add clip' -> selects outro asset ('1122') -> clicks 'Add media'."""
        print(f"\n[Flow] Adding outro clip ('{asset_name}')...")
        
        # Dismiss any overlays
        self.page.keyboard.press("Escape")
        time.sleep(1)
        
        # 1. Click '+' at timeline end
        plus_btn = self.page.locator('button[aria-label="Add clip"]').first
        plus_btn.click()
        time.sleep(1)
        
        # 2. Click '+ Add clip'
        add_clip_btn = self.page.locator('[role="menuitem"]:has-text("Add clip"), button:has-text("Add clip")').first
        add_clip_btn.click()
        time.sleep(2)
        
        # 3. Select asset in drawer
        asset_item = self.page.locator(f'button:has-text("{asset_name}"), div:has-text("{asset_name}")').first
        if asset_item.count() > 0 and asset_item.is_visible():
            print(f"[Flow] Found asset '{asset_name}', selecting it...")
            asset_item.click()
            time.sleep(1)
            
        # 4. Click 'Add media' button
        add_media_btn = self.page.locator('button:has-text("Add media")').first
        add_media_btn.wait_for(state="visible", timeout=15000)
        add_media_btn.click()
        print("[Flow] Outro clip added to timeline successfully!")
        time.sleep(2)

    def download_final_video(self, filename: str = "sheru_final_complete.mp4") -> Path:
        """Clicks the download icon in the top header and saves the file."""
        print("\n[Flow] Downloading finished video...")
        dest_path = OUTPUT_DIR / filename
        
        self.page.keyboard.press("Escape")
        time.sleep(1)
        
        dl_button = self.page.locator('button[aria-label="Download scene"], button:has-text("download")').first
        dl_button.click(force=True)
        print("[Flow] Triggered Download scene button!")
        time.sleep(3)
        return dest_path
