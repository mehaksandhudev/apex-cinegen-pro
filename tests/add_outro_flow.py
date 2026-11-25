import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    flow_page.bring_to_front()
    
    # Click plus button at the end of timeline
    print("Clicking plus button...")
    flow_page.evaluate("document.querySelector('button[aria-label=\"Add clip\"]').click()")
    time.sleep(1)
    
    # Click Add clip menuitem
    add_clip = flow_page.locator('[role="menuitem"]:has-text("Add clip")').first
    if add_clip.is_visible():
        print("Clicking 'Add clip' menu item...")
        add_clip.click()
        time.sleep(2)
        
        # Inspect the modal or picker that opened
        js_inspect = """() => {
            const dialog = document.querySelector('[role="dialog"], mat-dialog-container, .cdk-overlay-pane');
            const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(i => i.outerHTML);
            const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText.trim(),
                label: b.getAttribute('aria-label') || ''
            })).filter(b => b.text || b.label);
            const allText = dialog ? dialog.innerText : document.body.innerText.slice(0, 1000);
            return {
                hasDialog: !!dialog,
                allText: allText.slice(0, 800),
                fileInputs,
                buttons: buttons.slice(0, 25)
            };
        }"""
        res = flow_page.evaluate(js_inspect)
        print("Add clip modal inspect:\n", res)
    else:
        print("Add clip menu item not visible!")
