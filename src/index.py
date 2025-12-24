import csv
import os
from datetime import datetime, date
from typing import Optional, Dict
import httpx

def parse_date(value: str) -> Optional[date]:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y %I:%M %p", "%m/%d/%Y %I:%M %p"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None

def load_today_row(csv_content: str, date_col: str) -> Optional[Dict[str, str]]:
    # IST = UTC+5:30
    today_ist = (datetime.utcnow().replace(hour=(datetime.utcnow().hour + 5) % 24, 
                                           minute=(datetime.utcnow().minute + 30) % 60)).date()
    
    lines = csv_content.strip().split('\n')
    reader = csv.DictReader(lines)
    
    for row in reader:
        raw = row.get(date_col) or row.get("Date") or row.get("f1")
        if not raw:
            continue
        d = parse_date(str(raw))
        if d == today_ist:
            return row
    return None

def format_message(row: Dict[str, str], env: dict) -> str:
    category = row.get(env.get("CSV_CATEGORY_COLUMN", "Topic/Category")) or "Unknown"
    problem = row.get(env.get("CSV_PROBLEM_COLUMN", "Question Title")) or "Unnamed Problem"
    difficulty = row.get(env.get("CSV_DIFFICULTY_COLUMN", "Difficulty")) or "Unknown"
    description = row.get(env.get("CSV_DESCRIPTION_COLUMN", "Question Description")) or "No description."
    url = row.get(env.get("CSV_URL_COLUMN", "url")) or ""
    
    prefix = env.get("DAILY_DSA_PREFIX_TEXT", "Ready to sharpen your problem-solving skills? Rise and grind!")
    
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
    # Cron trigger handler
    try:
        # Read CSV from KV or R2 (you'll need to set this up)
        # For now, assume it's in the code or fetched from somewhere
        csv_path = env.get("QUESTIONS_CSV_PATH", "questions.csv")
        
        # You need to upload questions.csv to KV or R2
        # Example: csv_content = await env.KV_NAMESPACE.get("questions.csv")
        # For now, return error message
        
        webhook_url = env.DISCORD_WEBHOOK_URL
        date_col = env.get("CSV_DATE_COLUMN", "Date")
        
        # Placeholder - you need to fetch CSV content
        return Response("Cron job triggered. CSV loading not implemented yet.", status=200)
        
        # Once CSV is available:
        # row = load_today_row(csv_content, date_col)
        # if not row:
        #     return Response("No problem for today", status=200)
        # 
        # content = format_message(row, env)
        # 
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(webhook_url, json={"content": content})
        #     return Response(f"Posted: {response.status_code}", status=200)
        
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

# Cloudflare Workers entry point
async def fetch(request, env, ctx):
    return await on_fetch(request, env)
