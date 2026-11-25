"""
Main Orchestration Script for Sheru Bhai Video Automation
Fully tested and calibrated end-to-end pipeline:
1. ChatGPT prompt generation (Phase 1 & Phase 2)
2. Google Flow Clip 1 generation
3. Google Flow Extend with Clip 2 (10s slider calibrated)
4. Outro insertion (Asset '1122')
5. Final video download
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import CHROME_PROFILE_DIR, OUTRO_METHOD, DEFAULT_TOPIC_NUMBER, OUTPUT_DIR
from chatgpt_agent import ChatGPTAgent
from flow_agent import FlowAgent

def get_or_create_page(context, url_substring, target_url):
    """Finds an existing page matching url_substring or opens target_url."""
    for p in context.pages:
        try:
            if url_substring in p.url:
                print(f"[*] Found existing tab: {p.url[:60]}...")
                return p
        except Exception:
            pass
    print(f"[*] Opening new tab for: {target_url}...")
    p = context.new_page()
    p.goto(target_url)
    return p

def run_automation():
    print("\n" + "="*60)
    print("      SHERU BHAI AUTOMATION PIPELINE")
    print("="*60 + "\n")
    
    with sync_playwright() as p:
        print("[*] Connecting to Chrome via CDP (port 9222)...")
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            print("[✓] Connected to your active Chrome browser!")
        except Exception as e:
            print(f"[!] Could not connect to port 9222: {e}")
            print("[!] Please run 'launch_my_chrome_for_automation.bat' first.")
            return

        # ----------------------------------------------------
        # STEP 1: CHATGPT PROMPT GENERATION
        # ----------------------------------------------------
        print("\n--- STEP 1: CHATGPT PROMPT GENERATION ---")
        chatgpt_page = get_or_create_page(context, "chatgpt.com", "https://chatgpt.com")
        chatgpt_page.bring_to_front()
        chatgpt = ChatGPTAgent(chatgpt_page)
        
        # Check if user wants fresh generation or use active chat
        existing_clips = chatgpt.extract_clip_prompts()
        if len(existing_clips) >= 2:
            print(f"[✓] Using generated prompts from active ChatGPT chat!")
            clip1_prompt = existing_clips[0]
            clip2_prompt = existing_clips[1]
        else:
            print("[*] Generating new prompts from ChatGPT...")
            ideas_response = chatgpt.run_phase_1()
            
            if DEFAULT_TOPIC_NUMBER == 'ask':
                topic_choice = input("\nEnter topic number (1-10) [Default: 1]: ").strip() or "1"
            else:
                topic_choice = str(DEFAULT_TOPIC_NUMBER)
                
            clip_prompts = chatgpt.run_phase_2(topic_choice)
            if len(clip_prompts) < 2:
                print("[!] Error: Could not extract at least 2 clip prompts from ChatGPT.")
                return
            clip1_prompt = clip_prompts[0]
            clip2_prompt = clip_prompts[1]

        print("\n" + "="*60)
        print("★ [CLIP 1 PROMPT FULL] (" + str(len(clip1_prompt)) + " chars):\n" + clip1_prompt)
        print("="*60)
        print("★ [CLIP 2 PROMPT FULL] (" + str(len(clip2_prompt)) + " chars):\n" + clip2_prompt)
        print("="*60 + "\n")

        # ----------------------------------------------------
        # STEP 2: GOOGLE FLOW VIDEO STUDIO
        # ----------------------------------------------------
        print("\n--- STEP 2: GOOGLE FLOW STUDIO ---")
        flow_page = None
        for page in context.pages:
            if "flow.google.com/project" in page.url:
                flow_page = page
                break
        if not flow_page:
            flow_page = get_or_create_page(context, "flow.google.com", "https://flow.google.com")
            
        flow_page.bring_to_front()
        flow = FlowAgent(flow_page)
        
        # 1. Start new project if not inside editor
        flow.create_new_project()
        
        # 2. Generate Clip 1
        flow.generate_clip_1(clip1_prompt)
        
        # 3. Extend with Clip 2 (10 seconds)
        flow.extend_with_clip_2(clip2_prompt)
        
        # 4. Add Outro Clip (Asset '1122')
        flow.add_outro_clip(asset_name="1122")
        
        # 5. Download final complete video
        flow.download_final_video("sheru_final_complete.mp4")
            
        print("\n" + "="*60)
        print(" [🎉 SUCCESS 🎉] Entire Sheru Bhai video generation pipeline finished!")
        print("="*60 + "\n")

if __name__ == "__main__":
    run_automation()
