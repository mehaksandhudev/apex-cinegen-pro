import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    flow_page.bring_to_front()
    
    # Click Download media button
    dl_btn = flow_page.locator('button[aria-label="Download media"], button[aria-label="Download scene"]').first
    print("Download button visible:", dl_btn.is_visible())
    dl_btn.click(force=True)
    time.sleep(1)
    
    # Check what menu items appeared
    items = flow_page.locator('[role="menuitem"], .mat-mdc-menu-item').all()
    print("Found menu items count:", len(items))
    for it in items:
        txt = it.inner_text().strip()
        print("  Item:", repr(txt))
        if "720p" in txt or "Original" in txt:
            print("  --> Clicking 720p option!")
            it.click(force=True)
            print("  [✓] CLICKED 720p!")
            break
