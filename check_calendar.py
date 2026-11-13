import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://reserve.fumotoppara.net/reserved/reserved-calendar-list"
OUT = Path("diagnostics")
OUT.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(URL, wait_until="networkidle", timeout=60000)
        await page.screenshot(path=str(OUT / "calendar.png"), full_page=True)

        data = await page.evaluate("""() => {
          const tables = [...document.querySelectorAll('table')];
          return {
            title: document.title,
            body_has_dec31: document.body.innerText.includes('12/31'),
            tables: tables.map((table, index) => ({
              index,
              rows: [...table.querySelectorAll('tr')].map(row =>
                [...row.querySelectorAll('th,td')].map(cell => ({
                  text: cell.innerText.trim(),
                  html: cell.outerHTML.slice(0, 1000)
                }))
              )
            })),
            matching_elements: [...document.querySelectorAll('body *')]
              .filter(el => el.children.length === 0 &&
                (el.textContent || '').trim() === '12/31')
              .slice(0, 10).map(el => ({
                html: el.parentElement?.outerHTML.slice(0, 4000)
              }))
          };
        }""")

        result = {
            "http_status": response.status if response else None,
            "data": data,
            "availability_confirmed": False
        }
        (OUT / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("December 31 found:", data["body_has_dec31"])
        print("Tables:", len(data["tables"]))
        print("Diagnostic saved. No availability notification.")
        await browser.close()

asyncio.run(main())
