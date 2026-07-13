import os
from selenium import webdriver
from selenium.webdriver.safari.options import Options


def main():
    print("Initializing Safari Webdriver (native macOS)...")
    options = Options()
    # Safari supports native automation out-of-the-box on macOS.
    driver = webdriver.Safari(options=options)

    try:
        print("Navigating to http://localhost:8000/index.html...")
        driver.get("http://localhost:8000/index.html")

        # Maximize to get a nice desktop layout screenshot
        driver.maximize_window()

        screenshot_path = "docs_safari_preview.png"
        driver.save_screenshot(screenshot_path)
        print(
            f"\n🎉 Success! Screenshot saved to current directory as: {os.path.abspath(screenshot_path)}"
        )
    except Exception as e:
        print(f"\n❌ Error launching Safari: {e}")
        print(
            "Note: If Safaridriver is not enabled, you can enable it by running: sudo safaridriver --enable"
        )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
