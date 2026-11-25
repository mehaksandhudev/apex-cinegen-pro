from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    
    # Check what text and attributes are on the right tile
    js = """() => {
        const tiles = Array.from(document.querySelectorAll('flow-video-tile, .thumbnail, [role="button"], mat-card, .scene-card')).map(el => ({
            tag: el.tagName,
            cls: el.className,
            text: el.innerText.trim(),
            aria: el.getAttribute('aria-label')
        }));
        
        // Check timeline clips
        const clips = Array.from(document.querySelectorAll('.timeline-clip, [class*="clip"]')).map(el => ({
            cls: el.className,
            text: el.innerText.trim()
        }));
        
        return {
            url: window.location.href,
            tiles: tiles.slice(0, 10),
            clips: clips.slice(0, 10)
        };
    }"""
    print(flow_page.evaluate(js))
