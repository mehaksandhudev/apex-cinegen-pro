from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    pages = context.pages
    print(f"Connected to Chrome! {len(pages)} open tabs:")
    for i, pg in enumerate(pages):
        print(f"  [{i+1}] {pg.title()} | {pg.url}")

    # Find or navigate to YouTube Studio
    yt_page = None
    for pg in pages:
        if "studio.youtube.com" in pg.url:
            yt_page = pg
            break

    if not yt_page:
        yt_page = context.new_page()
        print("\nOpening YouTube Studio in new tab...")
        yt_page.goto("https://studio.youtube.com", timeout=30000)

    yt_page.bring_to_front()
    yt_page.wait_for_timeout(4000)

    print("\n--- YouTube Studio Tab Info ---")
    print("URL:", yt_page.url)
    print("Title:", yt_page.title())

    # Check Channel Name / Entity details
    channel_name_el = yt_page.locator("#entity-name, #channel-name, .channel-title, [id='channel-title']").all()
    channel_names = [el.inner_text().strip() for el in channel_name_el if el.inner_text().strip()]
    print("Channel name elements:", channel_names)

    # Check Create button (verification that user is logged in as Creator)
    create_btn = yt_page.locator('#create-icon, button:has-text("Create"), [aria-label="Create"]').first
    is_logged_in = create_btn.count() > 0 and create_btn.is_visible()
    print("Create / Upload button visible:", is_logged_in)

    # Check Channel ID in URL
    if "/channel/" in yt_page.url:
        cid = yt_page.url.split("/channel/")[1].split("/")[0]
        print("Channel ID:", cid)
