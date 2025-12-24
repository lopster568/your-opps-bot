from js import Response, fetch
import csv
from datetime import datetime, date, timedelta
from io import StringIO

def parse_date(value):
    value = value.strip()
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y %I:%M %p", "%m/%d/%Y %I:%M %p"]:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None

def get_today_ist():
    # IST = UTC+5:30
    utc_now = datetime.utcnow()
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    return ist_now.date()

def load_today_row(csv_content, date_col):
    today = get_today_ist()
    reader = csv.DictReader(StringIO(csv_content))
    
    for row in reader:
        raw = row.get(date_col) or row.get("Date") or row.get("f1")
        if not raw:
            continue
        d = parse_date(str(raw))
        if d == today:
            return row
    return None

def format_message(row, env):
    category = row.get(env.CSV_CATEGORY_COLUMN) or "Unknown"
    problem = row.get(env.CSV_PROBLEM_COLUMN) or "Unnamed Problem"
    difficulty = row.get(env.CSV_DIFFICULTY_COLUMN) or "Unknown"
    description = row.get(env.CSV_DESCRIPTION_COLUMN) or "No description."
    url = row.get(env.CSV_URL_COLUMN) or ""
    
    prefix = getattr(env, "DAILY_DSA_PREFIX_TEXT", "Ready to sharpen your problem-solving skills? Rise and grind!")
    
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

async def on_fetch(request, env):
    # Handle scheduled cron trigger
    try:
        webhook_url = env.DISCORD_WEBHOOK_URL
        date_col = getattr(env, "CSV_DATE_COLUMN", "Date")
        
        # Fetch CSV from GitHub raw or paste content
        csv_url = getattr(env, "CSV_URL", None)
        if not csv_url:
            return Response.new("CSV_URL not configured", status=500)
        
        response = await fetch(csv_url)
        csv_content = await response.text()
        
        row = load_today_row(csv_content, date_col)
        if not row:
            return Response.new("No problem for today", status=200)
        
        content = format_message(row, env)
        
        # Post to Discord webhook
        webhook_response = await fetch(webhook_url, {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"content": {repr(content)}}}'
        })
        
        return Response.new(f"Posted successfully: {webhook_response.status}", status=200)
        
    except Exception as e:
        return Response.new(f"Error: {str(e)}", status=500)
