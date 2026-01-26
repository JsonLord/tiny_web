
from playwright.sync_api import sync_playwright
import re

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        with open("playwright_log.txt", "w") as log_file:
            log_file.write("THOUGHTS; VISION; ACTIONS\\n")
            log_file.write("I need to find the latest events on dawnmauricio.com. I will navigate to the events page and extract the events listed there.\\n")

            log_file.write("ACTION: Navigating directly to https://dawnmauricio.com/events\\n")
            page.goto("https://dawnmauricio.com/events", wait_until="networkidle", timeout=60000)
            log_file.write("ACTION: Successfully navigated to the events page.\\n")

            log_file.write("THOUGHT: Now I am on the events page. I will extract the text from the page to find the events.\\n")

            # Get the text of the entire page
            page_text = page.locator('body').inner_text()
            log_file.write(f"ACTION: Extracted the following text from the page:\\n{page_text}\\n")

        browser.close()

if __name__ == "__main__":
    run()
