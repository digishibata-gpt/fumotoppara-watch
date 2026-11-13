import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://reserve.fumotoppara.net/reserved/reserved-calendar-list"
TARGET_DATE = "12/31"
TARGET_ITEM = "キャンプ宿泊"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        response = await page.goto(
            URL, wait_until="networkidle", timeout=60000
        )

        if not response or response.status != 200:
            raise RuntimeError("Calendar could not be loaded")

        result = await page.evaluate("""({date, item}) => {
            for (const table of document.querySelectorAll('table')) {
                const rows = [...table.querySelectorAll('tr')];
                const headers = [...rows[0]?.querySelectorAll('th,td') || []];
                const column = headers.findIndex(cell =>
                    cell.innerText.trim().split(/\\s+/)[0] === date
                );
                if (column < 0) continue;
                for (const row of rows.slice(1)) {
                    const cells = [...row.querySelectorAll('th,td')];
                    if (cells[0]?.innerText.trim() !== item) continue;
                    return {
                        date, item,
                        symbol: cells[column]?.innerText.trim() ?? null,
                        found: true
                    };
                }
            }
            return {date, item, symbol: null, found: false};
        }""", {"date": TARGET_DATE, "item": TARGET_ITEM})

        Path("diagnostics").mkdir(exist_ok=True)
        Path("diagnostics/result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        symbol = result["symbol"]
        if not result["found"] or symbol is None:
            raise RuntimeError("Target date or item not found")

        print("Date:", TARGET_DATE)
        print("Item:", TARGET_ITEM)
        print("Public calendar symbol:", symbol)

        if symbol in ("○", "△"):
            print("CANDIDATE: Check actual booking availability")
        elif symbol == "×":
            print("FULL: No public calendar availability")
        else:
            print("UNKNOWN: No availability conclusion")

        print("Booking availability is NOT confirmed.")
        await browser.close()

asyncio.run(main())

# Gmail送信テスト（手動実行時のみ）
import os
import smtplib
from email.message import EmailMessage

if os.environ.get("MAIL_TEST") == "1":
    address = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]

    message = EmailMessage()
    message["From"] = address
    message["To"] = address
    message["Subject"] = "ふもとっぱら空き監視：メール送信テスト"
    message.set_content("Gmail通知の接続テストに成功しました。これは空き通知ではありません。")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(address, password)
        smtp.send_message(message)

    print("Gmail test message sent.")
