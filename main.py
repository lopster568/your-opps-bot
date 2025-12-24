import os
from dotenv import load_dotenv
import discord
from dsa_scheduler import start_daily_dsa_job, send_startup_test_message

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    # Start the daily DSA scheduler once the client is ready
    start_daily_dsa_job(client)
    # Send a startup test message to the configured startup channel
    await send_startup_test_message(client)

@client.event
async def on_message(message):
    print(message.content)
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("Missing DISCORD_TOKEN in environment (.env)")

client.run(token)
