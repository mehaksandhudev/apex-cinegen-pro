"""
ChatGPT Automation Module
Interacts with ChatGPT web interface to generate viral story ideas and clip prompts.
"""

import time
import re
from playwright.sync_api import Page
from config import MASTER_PROMPT_TEMPLATE, VIDEO_DURATION

class ChatGPTAgent:
    def __init__(self, page: Page):
        self.page = page

    def wait_for_response(self, timeout_sec: int = 120):
        """Waits for ChatGPT to finish generating its response."""
        time.sleep(3)
        stop_btn_selector = 'button[data-testid="stop-button"], button[aria-label="Stop streaming"], button[aria-label="Stop generating"]'
        start_time = time.time()
        
        while time.time() - start_time < timeout_sec:
            try:
                stop_btn = self.page.locator(stop_btn_selector)
                if stop_btn.count() > 0 and stop_btn.first.is_visible():
                    time.sleep(1)
                    continue
            except Exception:
                pass
            
            # Check if send button is active / present
            send_btn = self.page.locator('button[data-testid="send-button"]')
            if send_btn.count() > 0 and send_btn.first.is_visible():
                time.sleep(2)
                break
            time.sleep(1)

    def send_prompt(self, text: str):
        """Sends a message into the ChatGPT prompt box."""
        textarea = self.page.locator('#prompt-textarea')
        if textarea.count() == 0:
            textarea = self.page.locator('div[contenteditable="true"]')
        
        textarea.wait_for(state="visible", timeout=15000)
        textarea.click()
        textarea.fill(text)
        time.sleep(0.5)
        
        send_btn = self.page.locator('button[data-testid="send-button"]')
        if send_btn.count() > 0 and send_btn.first.is_visible():
            send_btn.first.click()
        else:
            textarea.press("Enter")
        
        print("[ChatGPT] Prompt sent, waiting for response...")
        self.wait_for_response()

    def get_full_chat_text(self) -> str:
        """Returns the full text from the main conversation container."""
        return self.page.locator('main').inner_text()

    def extract_clip_prompts(self) -> list[str]:
        """Extracts the 100% full Clip 1, Clip 2 (and Clip 3) prompts from code blocks."""
        # Method 1: Large code tags (> 100 characters) - matches the Plain Text code blocks perfectly
        large_code_blocks = [
            x.inner_text().strip()
            for x in self.page.locator('code').all()
            if len(x.inner_text().strip()) > 100
        ]
        
        needed_count = 2 if "20" in VIDEO_DURATION else 3
        if len(large_code_blocks) >= needed_count:
            return large_code_blocks[-needed_count:]
            
        # Method 2: Fallback regex on the latest assistant turn
        full_text = self.get_full_chat_text()
        last_reply = full_text.split("ChatGPT said:")[-1]
        
        clips = []
        m1 = re.search(r'Clip\s*1[^\n]*\n(?:Plain text\n)?(.*?)(?=Clip\s*2)', last_reply, re.DOTALL | re.IGNORECASE)
        if m1:
            clips.append(m1.group(1).strip('`\n\r '))
            
        m2 = re.search(r'Clip\s*2[^\n]*\n(?:Plain text\n)?(.*?)(?=\n(?:Clip\s*3|This might|ChatGPT can|Ad options|\Z))', last_reply, re.DOTALL | re.IGNORECASE)
        if m2:
            clips.append(m2.group(1).strip('`\n\r '))
            
        m3 = re.search(r'Clip\s*3[^\n]*\n(?:Plain text\n)?(.*?)(?=\n(?:This might|ChatGPT can|Ad options|\Z))', last_reply, re.DOTALL | re.IGNORECASE)
        if m3:
            clips.append(m3.group(1).strip('`\n\r '))
            
        return clips

    def run_phase_1(self) -> str:
        """Sends the Master Prompt and returns the 10 ideas."""
        prompt = MASTER_PROMPT_TEMPLATE.replace("{VIDEO_DURATION}", VIDEO_DURATION)
        print("[ChatGPT] Starting Phase 1: Generating 10 viral story ideas...")
        self.send_prompt(prompt)
        return self.get_full_chat_text()

    def run_phase_2(self, topic_choice: str) -> list[str]:
        """Sends the selected topic number and extracts full clip prompts."""
        print(f"[ChatGPT] Starting Phase 2: Requesting prompts for topic: '{topic_choice}'...")
        self.send_prompt(str(topic_choice))
        clips = self.extract_clip_prompts()
        print(f"[ChatGPT] Extracted {len(clips)} full clip prompts successfully.")
        return clips
