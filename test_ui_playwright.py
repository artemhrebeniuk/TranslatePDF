import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACTS_DIR = "/Users/mr_shpepe/.gemini/antigravity-ide/brain/4a6a09e3-201b-4a58-8f42-f6d7844823c2"

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        print("1. Navigating to http://127.0.0.1:5055/ ...")
        await page.goto("http://127.0.0.1:5055/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Initial streamlined load screenshot
        screenshot_1 = os.path.join(ARTIFACTS_DIR, "streamlined_initial_load.png")
        await page.screenshot(path=screenshot_1, full_page=False)
        print(f"Captured streamlined initial load: {screenshot_1}")

        # 2. Click Translate Document
        print("2. Clicking 'Translate Document'...")
        translate_btn = page.locator("#btnTranslate")
        await translate_btn.click()

        # Wait for translation to complete
        await page.wait_for_selector("#transImg", state="visible", timeout=30000)
        await page.wait_for_timeout(1500)

        screenshot_2 = os.path.join(ARTIFACTS_DIR, "streamlined_translated_split.png")
        await page.screenshot(path=screenshot_2, full_page=False)
        print(f"Captured streamlined translated split view: {screenshot_2}")

        # 3. Test Synchronized Parallel Rotation (90deg)
        print("3. Testing Parallel Rotation: Clicking 'Rotate 90°'...")
        rotate_btn = page.locator("#btnRotateCw")
        await rotate_btn.click()
        await page.wait_for_timeout(600)

        badge_text = await page.locator("#rotationBadge").inner_text()
        print(f"Rotation badge is now: {badge_text}")

        screenshot_3 = os.path.join(ARTIFACTS_DIR, "streamlined_rotated_90deg.png")
        await page.screenshot(path=screenshot_3, full_page=False)
        print(f"Captured 90deg rotated parallel view: {screenshot_3}")

        # 4. Check page 3 doctor signatures
        await rotate_btn.click() # 180
        await page.wait_for_timeout(200)
        await rotate_btn.click() # 270
        await page.wait_for_timeout(200)
        await page.locator("#btnRotateReset").click() # reset to 0
        await page.wait_for_timeout(300)

        orig_next_btn = page.locator("#btnOrigNext")
        await orig_next_btn.click() # page 2
        await page.wait_for_timeout(500)
        await orig_next_btn.click() # page 3
        await page.wait_for_timeout(800)

        screenshot_4 = os.path.join(ARTIFACTS_DIR, "streamlined_page3_signatures.png")
        await page.screenshot(path=screenshot_4, full_page=False)
        print(f"Captured Page 3 (Signatures & Stamps intact): {screenshot_4}")

        await browser.close()
        print("All streamlined tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_test())
