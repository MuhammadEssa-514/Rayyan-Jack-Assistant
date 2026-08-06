"""
Jack AI Windows Agent — Browser Automation
Uses Playwright for reliable browser control.
"""
import asyncio
import threading
import subprocess
import urllib.parse
from loguru import logger

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available: pip install playwright && playwright install chromium")


SEARCH_ENGINES = {
    "google":  "https://www.google.com/search?q=",
    "youtube": "https://www.youtube.com/results?search_query=",
    "bing":    "https://www.bing.com/search?q=",
}


class BrowserController:

    def open_url(self, params: dict) -> dict:
        """Open a URL in the default browser."""
        url = params.get("url", "")
        if not url:
            return {"success": False, "message": "URL den"}

        # Add https:// if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            # Use Windows default browser (fastest approach)
            subprocess.Popen(f'start "" "{url}"', shell=True)
            logger.success(f"✅ Browser mein khula: {url}")
            return {"success": True, "message": "Browser mein khul raha hai"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def search(self, params: dict) -> dict:
        """Search the web."""
        query = params.get("query", "")
        engine = params.get("engine", "google").lower()

        if not query:
            return {"success": False, "message": "Search query den"}

        base_url = SEARCH_ENGINES.get(engine, SEARCH_ENGINES["google"])
        url = base_url + urllib.parse.quote_plus(query)

        try:
            subprocess.Popen(f'start "" "{url}"', shell=True)
            logger.success(f"✅ Search: '{query}' on {engine}")
            return {"success": True, "message": f"'{query}' search ho raha hai"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def open_youtube(self, params: dict) -> dict:
        """Open YouTube, optionally with a search."""
        query = params.get("query", "")
        if query:
            return self.search({**params, "engine": "youtube"})
        return self.open_url({"url": "https://youtube.com"})

    def playwright_click(self, params: dict) -> dict:
        """
        Use Playwright to click an element on the current browser page.
        More reliable than mouse coordinates for web elements.
        (Used for complex browser interactions)
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "message": "Playwright install nahi hai"}

        selector = params.get("selector", "")
        text = params.get("text", "")
        url = params.get("url", "")

        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                context = browser.contexts[0]
                page = context.pages[0]

                if url:
                    page.goto(url)

                if text:
                    page.get_by_text(text).first.click()
                elif selector:
                    page.click(selector)

                return {"success": True, "message": "Click ho gaya"}
        except Exception as e:
            return {"success": False, "message": str(e)}
