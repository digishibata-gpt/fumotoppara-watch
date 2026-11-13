import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://reserve.fumotoppara.net/reserved/reserved-calendar-list"
OUT = Path("diagnostics")
OUT.mkdir(exist_ok=True)

async def main():
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": URL,
        "status": "unknown"
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1440, "height": 1100}
        )

        try:
            response = await page.goto(
                URL,
                wait_until="domcontentloaded",
                timeout=45000
            )
            result["http_status"] = response.status if response else None
            await page.wait_for_timeout(12000)

            body = await page.locator("body").inner_text(timeout=10000)
            result["body_excerpt"] = body[:12000]
            result["december_31_visible"] = bool(
                re.search(r"12\s*[/月]\s*31|12月31日|2026[-/]12[-/]31", body)
            )

            result["status"] = (
                "page_loaded"
                if result["december_31_visible"]
                else "target_not_verified"
            )

            await page.screenshot(
                path=str(OUT / "calendar.png"),
                full_page=True
            )

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"

        finally:
            await browser.close()

    (OUT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(main())
