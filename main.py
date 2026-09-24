import os
import random
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
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
CHECK_INTERVAL = 300  # 5 minutes

UPLOADS_PLAYLIST_ID = "UU" + YT_CHANNEL_ID[2:]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

last_video_id = None


# ---------- SLASH COMMANDS ----------

@tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("nah bro i aint giving you the satisfaction")


@tree.command(name="rickroll", description="You know what this does")
async def rickroll(interaction: discord.Interaction):
    await interaction.response.send_message("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@tree.command(name="latestvideo", description="Get the latest video from the YouTube channel")
async def latestvideo(interaction: discord.Interaction):
    await interaction.response.defer()
    async with aiohttp.ClientSession() as session:
        video_id, title = await get_latest_video(session)
        await interaction.followup.send(f"🎥 **{title}**\nhttps://youtu.be/{video_id}")


# ---------- WELCOME MESSAGE ----------

def ordinal_suffix(n):
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


@client.event
async def on_member_join(member):
    channel = client.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        return

    member_count = member.guild.member_count
    color = discord.Color(random.randint(0, 0xFFFFFF))

    embed = discord.Embed(
        description=f"Welcome **{member}**\nto **{member.guild.name}** you are the {member_count}{ordinal_suffix(member_count)} member!",
        color=color
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(
        f"Welcome {member.mention} to **{member.guild.name}**! You are the {member_count}{ordinal_suffix(member_count)} member!",
        embed=embed
    )


# ---------- YOUTUBE UPLOAD WATCHER ----------

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
        last_video_id = video_id  # skip announcing the existing latest video on startup

        while not client.is_closed():
            try:
                video_id, title = await get_latest_video(session)
                if video_id != last_video_id:
                    last_video_id = video_id
                    await channel.send(
                        f"@everyone NO WAY I JUST UPLOADED??? I CANT BELIEVE THIS TOO WATCH IT NOW **{title}**\n"
                        f"https://youtu.be/{video_id}"
                    )
            except Exception as e:
                print(f"YouTube check failed: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


# ---------- STARTUP ----------

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_youtube_loop())


client.run(TOKEN)
