
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        with open("playwright_log.txt", "w", encoding="utf-8") as log_file:
            log_file.write("THOUGHTS; VISION; ACTIONS\\n")
            log_file.write("I need to extract detailed event information from dawnmauricio.com/events.\\n")

            log_file.write("ACTION: Navigating to https://dawnmauricio.com/events\\n")
            page.goto("https://dawnmauricio.com/events", wait_until="networkidle", timeout=60000)
            log_file.write("ACTION: Events page is fully loaded.\\n")

            log_file.write("THOUGHT: Now on the events page, I will dump the entire page HTML to get the event details.\\n")

            # Get the HTML of the entire page
            page_html = page.content()
            log_file.write(f"ACTION: Extracted the following HTML from the page:\\n{page_html}\\n")

        browser.close()

if __name__ == "__main__":
    run()
