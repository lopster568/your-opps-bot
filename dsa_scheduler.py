import os
import csv
from datetime import datetime, date
from typing import Optional, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
import discord

_IST = ZoneInfo("Asia/Kolkata")
_scheduler: Optional[AsyncIOScheduler] = None


def _parse_date(value: str) -> Optional[date]:
    value = value.strip()
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m/%d/%y %I:%M %p",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _load_today_row(csv_path: str, date_col: str) -> Optional[Dict[str, str]]:
    today_ist = datetime.now(tz=_IST).date()
    if not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # If file doesn't have headers, DictReader will use None; fallback by index names like f1, f2 ...
        for row in reader:
            # Support both named columns and fN indexes
            key = date_col if date_col in row else date_col
            raw = row.get(key) or row.get("f1") or row.get("date")
            if not raw:
                continue
            d = _parse_date(str(raw))
            if d == today_ist:
                return row
    return None


def _format_message(row: Dict[str, str]) -> str:
    # Column mapping with sensible defaults aligning to provided spec or common headers
    category = (
        row.get(os.getenv("CSV_CATEGORY_COLUMN", "f5"))
        or row.get("Topic/Category")
        or "Unknown"
    )
    problem = (
        row.get(os.getenv("CSV_PROBLEM_COLUMN", "f2"))
        or row.get("Question Title")
        or "Unnamed Problem"
    )
    difficulty = (
        row.get(os.getenv("CSV_DIFFICULTY_COLUMN", "f4"))
        or row.get("Difficulty")
        or "Unknown"
    )
    description = (
        row.get(os.getenv("CSV_DESCRIPTION_COLUMN", "f3"))
        or row.get("Question Description")
        or "No description."
    )
    url = (
        row.get(os.getenv("CSV_URL_COLUMN", "f9"))
        or row.get("url")
        or ""
    )

    prefix = os.getenv(
        "DAILY_DSA_PREFIX_TEXT",
        "Ready to sharpen your problem-solving skills? Rise and grind!",
    )

    lines = [
        "⭐ Daily DSA Problem ⭐",
        prefix,
        "",
        f"📌 Category: {category}",
        f"🧠 Problem: {problem}",
        f"⚡ Difficulty: {difficulty}",
        "📖 Problem Description:",
        f"{description}",
        f"🔗 Url: {url}" if url else "",
    ]
    return "\n".join([ln for ln in lines if ln])


async def _post_daily_dsa_problem(client: discord.Client) -> None:
    csv_path = os.getenv("QUESTIONS_CSV_PATH", "questions.csv")
    date_col = os.getenv("CSV_DATE_COLUMN", "f1")

    row = _load_today_row(csv_path, date_col)
    if not row:
        print(f"[Daily DSA] No row found for today's date in {csv_path} using column '{date_col}'.")
        return

    content = _format_message(row)

    channel = await _resolve_channel(client)

    if channel is None:
        print("[Daily DSA] No channel configured/found. Set DISCORD_CHANNEL_ID_DAILY_DSA or ensure a #daily-dsa channel exists.")
        return

    try:
        await channel.send(content)
        print("[Daily DSA] Posted today's problem.")
    except Exception as e:
        print(f"[Daily DSA] Failed to send message: {e}")


def start_daily_dsa_job(client: discord.Client) -> None:
    global _scheduler
    if _scheduler:
        return

    _scheduler = AsyncIOScheduler(timezone=_IST)

    # Start date: Dec 25, 2025 at 08:00 IST
    start_dt = datetime(2025, 12, 25, 8, 0, tzinfo=_IST)
    trigger = CronTrigger(hour=8, minute=0, timezone=_IST, start_date=start_dt)

    _scheduler.add_job(_post_daily_dsa_problem, trigger=trigger, args=[client], id="daily_dsa_problem")
    _scheduler.start()
    print("[Daily DSA] Scheduler started, daily job set for 08:00 IST.")


async def _resolve_channel(client: discord.Client) -> Optional[discord.abc.Messageable]:
    channel_id_env = os.getenv("DISCORD_CHANNEL_ID_DAILY_DSA")
    channel: Optional[discord.abc.Messageable] = None

    if channel_id_env:
        try:
            channel_id = int(channel_id_env)
            channel = await client.fetch_channel(channel_id)  # type: ignore
            return channel
        except Exception as e:
            print(f"[Daily DSA] Failed to fetch channel by id '{channel_id_env}': {e}")

    wanted_name = os.getenv("DISCORD_CHANNEL_NAME_DAILY_DSA", "daily-dsa").lower()
    for guild in client.guilds:
        for ch in getattr(guild, "text_channels", []):
            if getattr(ch, "name", "").lower() == wanted_name:
                return ch
    return None


async def send_startup_test_message(client: discord.Client) -> None:
    channel = await _resolve_channel(client)
    if channel is None:
        print("[Daily DSA] Startup test: No channel configured/found.")
        return

    now_ist = datetime.now(tz=_IST).strftime("%Y-%m-%d %H:%M:%S %Z")
    content = f"✅ Daily DSA Zap: Bot is online. ({now_ist})"
    try:
        await channel.send(content)
        print("[Daily DSA] Startup test message sent.")
    except Exception as e:
        print(f"[Daily DSA] Startup test failed to send: {e}")


def _find_row_for_date_or_next(csv_path: str, date_col: str, target_date: date) -> Optional[Dict[str, str]]:
    """Find the row for target_date; if not found, return the next upcoming row by date."""
    if not os.path.exists(csv_path):
        return None
    matches = []
    upcoming = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get(date_col) or row.get("f1") or row.get("date") or row.get("Date")
            if not raw:
                continue
            d = _parse_date(str(raw))
            if not d:
                continue
            if d == target_date:
                matches.append(row)
            elif d > target_date:
                upcoming.append((d, row))
    if matches:
        return matches[0]
    if upcoming:
        upcoming.sort(key=lambda t: t[0])
        return upcoming[0][1]
    return None


async def send_preview_daily_dsa_message(client: discord.Client) -> None:
    """Post a preview of the scheduled Daily DSA message (today or next available)."""
    csv_path = os.getenv("QUESTIONS_CSV_PATH", "questions.csv")
    date_col = os.getenv("CSV_DATE_COLUMN", "f1")

    # Allow overriding preview date via env; otherwise use today IST
    preview_str = os.getenv("PREVIEW_DATE")
    if preview_str:
        tgt = _parse_date(preview_str)
    else:
        tgt = datetime.now(tz=_IST).date()

    if not tgt:
        tgt = datetime.now(tz=_IST).date()

    row = _find_row_for_date_or_next(csv_path, date_col, tgt)
    if not row:
        print(f"[Daily DSA] Preview: No suitable row found in {csv_path} using column '{date_col}'.")
        return

    # Try to display the date associated with the row
    row_date_raw = row.get(date_col) or row.get("Date") or row.get("f1")
    row_date = _parse_date(str(row_date_raw)) if row_date_raw else None
    when_txt = row_date.isoformat() if row_date else "(unknown date)"

    content = _format_message(row)
    preview_header = f"👀 Preview: Daily DSA (scheduled for {when_txt} IST)"
    message = f"{preview_header}\n\n{content}"

    channel = await _resolve_channel(client)
    if channel is None:
        print("[Daily DSA] Preview: No channel configured/found.")
        return

    try:
        await channel.send(message)
        print("[Daily DSA] Preview message sent.")
    except Exception as e:
        print(f"[Daily DSA] Preview failed to send: {e}")
