import asyncio
import json
import os
import re
import smtplib
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright

URL = "https://reserve.fumotoppara.net/reserved/reserved-calendar-list"
TARGET = date(2026, 12, 31)
ITEM = "キャンプ宿泊"
TOKYO = ZoneInfo("Asia/Tokyo")
WEEKDAYS = "月火水木金土日"
STATE = Path("notification_state.json")


def calendar_symbol(tables, today):
    first = today.replace(day=1)
    offset = (TARGET - first).days
    candidates = []

    for header, rows in tables:
        if today > TARGET or not 0 <= offset < len(header):
            continue
        days = (first + timedelta(days=i) for i in range(len(header)))
        expected = [
            [f"{day.month}/{day.day}", WEEKDAYS[day.weekday()]]
            for day in days
        ]
        if header == expected:
            candidates.extend(
                row[offset] if len(row) == len(header) else ""
                for row in rows
            )

    if len(candidates) != 1:
        return None
    value = candidates[0]
    if value in {"○", "〇"}:
        return "○"
    if re.fullmatch(r"△(?:\s*残\s*[1-9][0-9]*)?", value):
        return "△"
    return "×" if value == "×" else None


async def read_calendar():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page(timezone_id="Asia/Tokyo")
            response = await page.goto(
                URL, wait_until="domcontentloaded", timeout=60000
            )
            if not response or response.status != 200 or page.url != URL:
                raise RuntimeError("Calendar loading failed")
            await page.locator("th.cell-site").get_by_text(
                ITEM, exact=True
            ).first.wait_for(timeout=20000)
            return await page.evaluate(
                """item => [...document.querySelectorAll('
                            """item => [...document.querySelectorAll('table')]
                    .filter(table => table.getClientRects().length)
                    .filter(table => table.rows[0]?.cells[0]?.matches('th.cell-corner'))
                    .map(table => {
                        const [header, ...rows] = table.rows;
                        const plain = cell => cell.colSpan === 1 && cell.rowSpan === 1;
                        const dates = [...header.cells].slice(1).map(cell =>
                            plain(cell) && cell.matches('th.cell-date')
                                ? [...cell.querySelectorAll(':scope > p')].map(p => p.innerText.trim())
                                : []);
                        const statuses = rows.filter(row =>
                            row.cells[0]?.matches('th.cell-site') &&
                            row.cells[0].innerText.trim() === item
                        ).map(row => [...row.cells].every(plain)
                            ? [...row.cells].slice(1).map(cell =>
                                cell.matches('td.cell-date') ? cell.innerText.trim() : '')
                            : []);
                        return [dates, statuses];
                    })""",
                ITEM,
            )
        finally:
            await browser.close()


def send_mail(symbol):
    address = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    message = EmailMessage()
    message["From"] = address
    message["To"] = address
    message["Subject"] = "【ふもとっぱら】12月31日に空き候補"
    message.set_content(
        f"{TARGET}チェックインの「{ITEM}」が公開カレンダーで「{symbol}」になりました。\n\n"
        f"{URL}\n\n"
        "実際に予約できるかは、ログイン後の予約画面でご確認ください。"
    )
    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
    try:
        smtp.login(address, password)
        smtp.send_message(message)
    finally:
        smtp.close()


async def main():
    today = datetime.now(TOKYO).date()
    if today > TARGET:
        print("Target check-in date has passed")
        return

    symbol = calendar_symbol(await read_calendar(), today)
    print(f"{TARGET} / {ITEM}: {symbol!r}")
    if symbol is None:
        raise RuntimeError("Could not verify target cell; no email sent")

    was_available = False
    if STATE.exists():
        previous = json.loads(STATE.read_text(encoding="utf-8"))
        was_available = previous["available"]
        if type(was_available) is not bool:
            raise ValueError("Invalid notification state")

    available = symbol in {"○", "△"}
    if available and not was_available:
        send_mail(symbol)
        print("Availability email sent")
    else:
        print("No new availability email")

    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"available": available, "symbol": symbol}),
        encoding="utf-8",
    )
    temporary.replace(STATE)


if __name__ == "__main__":
    asyncio.run(main())
