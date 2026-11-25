from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    flow_page = [pg for pg in browser.contexts[0].pages if "flow.google.com" in pg.url][0]
    
    js = """() => {
        // Deep search including shadow roots
        function searchNode(node) {
            let res = [];
            if (!node) return res;
            
            // Check text
            if (node.nodeType === Node.TEXT_NODE) {
                if (node.nodeValue && node.nodeValue.includes('%')) {
                    res.push({ type: 'text', val: node.nodeValue.trim(), parent: node.parentElement?.tagName });
                }
            }
            
            // Check shadow root
            if (node.shadowRoot) {
                res = res.concat(searchNode(node.shadowRoot));
            }
            
            // Traverse children
            if (node.childNodes) {
                for (let child of node.childNodes) {
                    res = res.concat(searchNode(child));
                }
            }
            return res;
        }
        
        // Also check canvas or video elements
        const videos = Array.from(document.querySelectorAll('video')).map(v => ({
            src: v.src,
            duration: v.duration,
            paused: v.paused,
            readyState: v.readyState
        }));
        
        // Check timeline state
        const timeline = document.querySelector('.scene-timeline, [class*="timeline"]');
        const plusBtn = document.querySelector('button[aria-label="Add clip"]');
        
        return {
            pctFound: searchNode(document.body),
            videos,
            hasPlus: !!plusBtn && plusBtn.offsetParent !== null
        };
    }"""
    print(flow_page.evaluate(js))
