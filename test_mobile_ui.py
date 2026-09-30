import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/mr_shpepe/.gemini/antigravity-ide/brain/4a6a09e3-201b-4a58-8f42-f6d7844823c2"

async def test_mobile():
    async with async_playwright() as p:
        # iPhone 14 Pro viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()

        print("1. Opening mobile view at http://127.0.0.1:5055/ ...")
        await page.goto("http://127.0.0.1:5055/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Initial mobile load
        shot1 = os.path.join(ARTIFACTS_DIR, "mobile_initial_load.png")
        await page.screenshot(path=shot1, full_page=False)
        print(f"Captured mobile initial load: {shot1}")

        # 2. Click Translate Document
        print("2. Tapping 'Translate Document'...")
        await page.locator("#btnTranslate").click()
        await page.wait_for_selector("#transImg", state="visible", timeout=30000)
        await page.wait_for_timeout(1200)

        shot2 = os.path.join(ARTIFACTS_DIR, "mobile_translated_split.png")
        await page.screenshot(path=shot2, full_page=False)
        print(f"Captured mobile translated split view: {shot2}")

        # 3. Switch to 'Translated' tab only
        print("3. Switching to Translated tab...")
        await page.locator(".mode-tab[data-view='rev']").click()
        await page.wait_for_timeout(600)

        shot3 = os.path.join(ARTIFACTS_DIR, "mobile_single_translated.png")
        await page.screenshot(path=shot3, full_page=False)
        print(f"Captured mobile single translated tab: {shot3}")

        # 4. Rotate 90deg on mobile
        print("4. Testing 90deg rotation on mobile...")
        await page.locator("#btnRotateCw").click()
        await page.wait_for_timeout(600)

        shot4 = os.path.join(ARTIFACTS_DIR, "mobile_rotated_90deg.png")
        await page.screenshot(path=shot4, full_page=False)
        print(f"Captured mobile rotated 90deg: {shot4}")

        # 5. Reset rotation and navigate to page 3
        await page.locator("#btnRotateReset").click()
        await page.wait_for_timeout(300)
        await page.locator("#btnTransNext").click() # p2
        await page.wait_for_timeout(400)
        await page.locator("#btnTransNext").click() # p3
        await page.wait_for_timeout(600)

        shot5 = os.path.join(ARTIFACTS_DIR, "mobile_page3_signatures.png")
        await page.screenshot(path=shot5, full_page=False)
        print(f"Captured mobile page 3 signatures: {shot5}")

        await browser.close()
        print("Mobile visual testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_mobile())
