#!/bin/bash
# bin/browser-mac.sh
# Native macOS Browser Launching and Screenshot Wrapper

# Ensure we have the URL argument
if [ -z "$1" ]; then
    echo "Usage: $0 <url> [screenshot_output_path]"
    echo "Example: $0 http://localhost:8000 docs_preview.png"
    exit 1
fi

URL="$1"
SCREENSHOT="${2:-docs_preview.png}"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Error: Python virtual environment 'venv' not found."
    exit 1
fi

echo "🚀 Launching native macOS browser for: $URL"

# Execute a inline python script with playwright
venv/bin/python3 -c "
import asyncio
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = None
        # Try chromium
        try:
            browser = await p.chromium.launch(headless=True)
            print('✔ Chromium launched natively.')
        except Exception as e:
            # Fall back to native webkit (Safari engine)
            try:
                browser = await p.webkit.launch(headless=True)
                print('✔ Webkit launched natively.')
            except Exception as e2:
                print('❌ Failed to launch native browsers via Playwright.')
                print('Please run: venv/bin/playwright install chromium')
                sys.exit(1)
        
        if browser:
            page = await browser.new_page()
            try:
                await page.goto('$URL', wait_until='networkidle', timeout=10000)
                await page.screenshot(path='$SCREENSHOT', full_page=True)
                print('📸 Success! Full-page screenshot saved to: $SCREENSHOT')
            except Exception as e:
                print(f'❌ Failed to navigate or capture screenshot: {e}')
            finally:
                await browser.close()

asyncio.run(run())
"
