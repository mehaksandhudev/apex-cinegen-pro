from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    
    # Check what items or menus are open
    js = """() => {
        const text = document.body.innerText;
        const p720 = Array.from(document.querySelectorAll('*')).filter(el => el.children.length === 0 && el.innerText.includes('720p')).map(el => ({
            tag: el.tagName,
            text: el.innerText,
            visible: el.offsetParent !== null
        }));
        return { p720, url: window.location.href };
    }"""
    print(flow_page.evaluate(js))
