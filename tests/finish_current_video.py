import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    
    # 1. Attach Outro
    print("Clicking Add clip (+)...")
    plus_btn = flow_page.locator('button[aria-label="Add clip"]').first
    plus_btn.click()
    time.sleep(1.5)
    
    add_clip_item = flow_page.locator('[role="menuitem"]:has-text("Add clip"), button:has-text("Add clip")').first
    if add_clip_item.count() > 0 and add_clip_item.is_visible():
        print("Clicking 'Add clip' menu item...")
        add_clip_item.click()
        time.sleep(2)
        
        # Select 1122
        items = flow_page.locator(':has-text("1122")').all()
        for item in items:
            if item.is_visible():
                print("Selecting 1122 asset...")
                item.click()
                break
        time.sleep(1)
        
        add_media_btn = flow_page.locator('button:has-text("Add media")').first
        if add_media_btn.count() > 0 and add_media_btn.is_visible():
            for _ in range(20):
                if not add_media_btn.is_disabled():
                    add_media_btn.click()
                    print("Clicked 'Add media' button! Outro attached!")
                    break
                time.sleep(1)
        time.sleep(3)
        
    # 2. Download Media
    downloads_dir = Path.home() / "Downloads"
    before_files = set(downloads_dir.glob("*.*"))
    
    print("\nClicking Download media...")
    dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"], button:has-text("download")').first
    print("Found download button:", dl_btn.get_attribute("aria-label"))
    dl_btn.click(force=True)
    
    # Wait for download to start and complete
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
        
    output_final = Path("c:/Users/mehak/Desktop/sheru automation/output_videos/sheru_final_complete.mp4")
    if new_file:
        print(f"\n[SUCCESS] New download detected: {new_file.name} ({new_file.stat().st_size / (1024*1024):.2f} MB)")
        shutil.copy2(new_file, output_final)
        print(f"Copied to: {output_final}")
    else:
        print("\nNo new download detected within 60s.")
