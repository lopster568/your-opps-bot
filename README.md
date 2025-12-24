# Your Opps Bot

This bot reads configuration from a `.env` file using `python-dotenv` and posts a Daily DSA problem to Discord via a scheduled job.

## Setup

1. Create a virtual environment (optional but recommended).
2. Install dependencies.
3. Configure your `.env` file.
4. Run the bot.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your real token and channel/config
python main.py
```

## Environment Variables

- `DISCORD_TOKEN`: Discord Bot token used to authenticate the client.

## Daily DSA Zap

Posts a formatted daily DSA problem to Discord at 8:00 AM IST, starting Dec 25, 2025.

- Configure the channel either by ID (recommended) or by name:
  - `DISCORD_CHANNEL_ID_DAILY_DSA` (e.g., 123456789012345678)
  - `DISCORD_CHANNEL_NAME_DAILY_DSA` (fallback, default: `daily-dsa`)
- CSV source and columns:
  - `QUESTIONS_CSV_PATH` (default: `questions.csv`)
  - `CSV_DATE_COLUMN` (default: `f1`, example headers: `Date`)
  - `CSV_CATEGORY_COLUMN` (default: `f5`, example: `Topic/Category`)
  - `CSV_PROBLEM_COLUMN` (default: `f2`, example: `Question Title`)
  - `CSV_DIFFICULTY_COLUMN` (default: `f4`, example: `Difficulty`)
  - `CSV_DESCRIPTION_COLUMN` (default: `f3`, example: `Question Description`)
  - `CSV_URL_COLUMN` (default: `f9`, example: `url`)
- Optional message intro:
  - `DAILY_DSA_PREFIX_TEXT` (default: friendly, non-profane line)

The scheduler starts when the bot becomes ready and posts to the configured channel. Ensure your CSV contains an entry for the current date in IST.
