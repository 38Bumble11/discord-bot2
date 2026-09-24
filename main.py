import os
import asyncio
import aiohttp
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
YT_API_KEY = os.getenv("YOUTUBE_API_KEY")
YT_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))
CHECK_INTERVAL = 300  # 5 minutes

# Uploads playlist = channel ID with "UC" -> "UU"
UPLOADS_PLAYLIST_ID = "UU" + YT_CHANNEL_ID[2:]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

last_video_id = None


async def get_latest_video(session):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": UPLOADS_PLAYLIST_ID,
        "maxResults": 1,
        "key": YT_API_KEY,
    }
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        item = data["items"][0]["snippet"]
        video_id = item["resourceId"]["videoId"]
        title = item["title"]
        return video_id, title


async def check_youtube_loop():
    global last_video_id
    await client.wait_until_ready()
    channel = client.get_channel(NOTIFY_CHANNEL_ID)

    async with aiohttp.ClientSession() as session:
        video_id, _ = await get_latest_video(session)
        last_video_id = video_id  # don't ping on startup for the existing latest video

        while not client.is_closed():
            try:
                video_id, title = await get_latest_video(session)
                if video_id != last_video_id:
                    last_video_id = video_id
                    await channel.send(
                        f"@everyone NO WAY I POSTED A NEW VIDEO??? HOW DID I DO THAT??? **{title}**\n"
                        f"https://youtu.be/{video_id}"
                    )
            except Exception as e:
                print(f"YouTube check failed: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_youtube_loop())


client.run(TOKEN)
