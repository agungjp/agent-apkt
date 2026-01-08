#!/usr/bin/env python3
"""Quick test script to verify headless mode works with new wait_for fix."""

import asyncio
from playwright.async_api import async_playwright


async def test_headless():
    """Test headless mode with visible wait."""
    async with async_playwright() as p:
        # Launch in headless mode with viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            print("🌐 Loading test page...")
            # Load a page with select elements for testing
            await page.goto("https://new-apktss.pln.co.id/", wait_until="domcontentloaded")
            print(f"✓ Loaded: {page.url}")
            
            # Wait for any select element to appear
            selects = page.locator("select")
            count = await selects.count()
            print(f"✓ Found {count} select elements on page")
            
            # Try to find the specific select we need
            month_select = page.locator("select[name='vc-component-4']").first
            try:
                await month_select.wait_for(state="visible", timeout=5000)
                print("✓ Month select found and visible!")
                return True
            except Exception as e:
                print(f"✗ Month select not found: {e}")
                return False
                
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


if __name__ == "__main__":
    result = asyncio.run(test_headless())
    exit(0 if result else 1)
