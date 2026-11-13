import asyncio
import json
import os
import smtplib
from pathlib import Path
from email.message import EmailMessage
from playwright.async_api import async_playwright

URL = "https://reserve.fumotoppara.net/reserved/reserved-calendar-list"
DATE = "12/31"
ITEM = "キャンプ宿泊"
STATE = Path("notification_state.json")
AVAILABLE = {"○", "△"}

def send_mail(subject, body):
    address = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    msg = EmailMessage()
    msg["From"] = address
    msg["To"] = address
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(address, password)
        smtp.send_message(msg)

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            response = await page.goto(
                URL, wait_until="networkidle", timeout=60000
            )
            if not response or response.status != 200:
                raise RuntimeError("Calendar loading failed")
            result = await page.evaluate("""({date, item}) => {
                for (const table of document.querySelectorAll('table')) {
                    const rows = [...table.querySelectorAll('tr')];
                    if (!rows.length) continue;
                    const header = [...rows[0].querySelectorAll('th,td')];
                    const col = header.findIndex(c =>
                        c.innerText.trim().split(/\\s+/)[0] === date
                    );
                    if (col < 0) continue;
                    for (const row of rows.slice(1)) {
                        const cells = [...row.querySelectorAll('th,td')];
                        if (cells[0]?.innerText.trim() !== item) continue;
                        return cells[col]?.innerText.trim() ?? null;
                    }
                }
                return null;
            }""", {"date": DATE, "item": ITEM})
            return result
        finally:
            await browser.close()

async def main():
    symbol = await check()
    print("2026-12-31 / camp overnight:", repr(symbol))

    if symbol not in AVAILABLE and symbol != "×":
        print("Unknown calendar status; no notification")
        return

    previous = {}
    if STATE.exists():
        previous = json.loads(STATE.read_text(encoding="utf-8"))
    was_available = previous.get("available", False)
    is_available = symbol in AVAILABLE

    if is_available and not was_available:
        send_mail(
            "【ふもとっぱら】12月31日に空き候補！",
            f"2026年12月31日 キャンプ宿泊の公開表示が「{symbol}」になりました。\n\n"
            f"予約ページ：{URL}\n\n"
            "公開カレンダー上の空き候補です。実際に予約可能かは予約画面で確認してください。"
        )
        print("Availability candidate email sent")
    else:
        print("No new availability notification")

    STATE.write_text(
        json.dumps({"available": is_available, "symbol": symbol}),
        encoding="utf-8"
    )

asyncio.run(main())
