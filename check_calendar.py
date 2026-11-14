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
