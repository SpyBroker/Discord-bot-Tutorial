import os
import logging
from dotenv import load_dotenv
import asyncio
import yt_dlp
import discord
from discord.ext import commands
from collections import defaultdict

# 1. Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, root=True, level=logging.INFO)

# 2. Configure Intents
intents = discord.Intents.default()
intents.message_content = True

# 3. Initialize Bot
bot = commands.Bot(command_prefix='!', intents=intents)

queue_dict=defaultdict(list)

# YTDLP SETTINGS
ytdlp_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,  # Corrected typo from 'quite' to 'quiet'
    'default_search': 'ytsearch',
    # Added to prevent unnecessary downloading and speed up extraction
    'force_generic_extractor': True,
    'extractor_args': {'youtube': {'skip_formats': 'hls,dash'}}
}

# 🛠️ CRITICAL FIX: Ensure correct FFmpeg options for streaming.
# The parameters below guarantee the output is raw PCM audio (s16le)
# at the correct sample rate (48000 Hz) and channel count (2).
ffmpeg_opts = {
    'before_options':
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # Corrected typo in '-reconnect_streamed' spacing
    'options': '-vn'
    # -vn tells it to drop video stream. The other format options are implicitly handled by discord.py's FFmpegPCMAudio
}


@bot.event
async def on_ready():
    """Confirms the bot is logged in and ready."""
    print(f'✅ We are ready to go, {bot.user.name}')


# --- Command Definitions ---
@bot.command()
async def info(ctx):
    """Gives info about the bot commands."""
    embed = discord.Embed(
        title="🎵 Music Buddy",
        description="I can play music for yaa!",
        color=discord.Color.green()
    )
    embed.add_field(name="!play <song name or URL>", value="plays music from YouTube/Spotify", inline=False)
    embed.add_field(name="!pause", value="pause the song.", inline=False)
    embed.add_field(name="!resume", value="resume the song.", inline=False)
    embed.add_field(name="!stop", value="stop and leave the voice channel", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def play(ctx, *, query):
    """Plays music from a query or URL."""
    if not ctx.author.voice:
        return await ctx.send("❌ You must be in a voice channel!")

    channel = ctx.author.voice.channel
    if not ctx.voice_client:
      await channel.connect()

    vc = ctx.voice_client

    await ctx.send(f"🔍 Searching for **{query}**...")

    try:
        # 1. Extract Information
        # Use asyncio.to_thread for blocking operation (yt-dlp)
        info = await asyncio.to_thread(yt_dlp.YoutubeDL(ytdlp_opts).extract_info, query, download=False)

        if "entries" in info:
            # Handle search result or playlist entry
            info = info["entries"][0]

        # 2. Get the stream URL
        # yt-dlp guarantees 'url' is present if 'format': 'bestaudio/best' is used
        stream_url = info['url']
        title = info["title"]

    except Exception as e:
        print(f"yt-dlp error: {e}")
        # Log the error for debugging, send a friendly message to the user
        return await ctx.send(f"❌ Failed to load audio for **{query}**. The source may be unavailable or private.")

    # 3. Create the audio source and play
    source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_opts)

    if vc.is_playing():
        vc.stop()

    vc.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    )
    await ctx.send(f"🎶 Now playing: **{title}**")


@bot.command()
async def play_next(ctx):
    guild_id = ctx.guild.id

    if not queue_dict[guild_id]:
        await ctx.send("Queue completed👌")
        return  # No more songs

    query = queue_dict[guild_id][0]
    vc = ctx.voice_client or ctx.author.voice.channel.connect()

    await ctx.send(f"⏳ Loading: **{query}**")

    try:
        # 1. Extract Information
        # Use asyncio.to_thread for blocking operation (yt-dlp)
        info = await asyncio.to_thread(yt_dlp.YoutubeDL(ytdlp_opts).extract_info, query, download=False)

        if "entries" in info:
            # Handle search result or playlist entry
            info = info["entries"][0]

        # 2. Get the stream URL
        # yt-dlp guarantees 'url' is present if 'format': 'bestaudio/best' is used
        stream_url = info['url']
        title = info["title"]

        source =  discord.FFmpegPCMAudio(stream_url, **ffmpeg_opts)

    except Exception as e:
        print(f"yt-dlp error: {e}")
        # Log the error for debugging, send a friendly message to the user
        return await ctx.send(f"❌ Failed to load audio for **{query}**. The source may be unavailable or private.")

    vc.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    )

    await ctx.send(f"🎶 Now playing: **{title}**")


@bot.command()
async def queue(ctx, *, query):
    guild_id = ctx.guild.id
    vc = ctx.voice_client
    queue_dict[guild_id].append(query)

    # Add song to queue (store only the query, extraction happens later)
    await ctx.send(f"📌 Added to queue: **{query}**")

    # Display queue
    q_list = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(queue_dict[guild_id])])
    await ctx.send(f"🎶 Current Queue:\n{q_list}")

    # If nothing is playing, start playing the first song
    if not vc or not vc.is_playing():
        await play_next(ctx)


# --- Control Commands ---
@bot.command()
async def pause(ctx):
    """Pauses the current song."""
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ Paused")
    elif not vc:
        await ctx.send("❌ Not connected to a voice channel.")


@bot.command()
async def resume(ctx):
    """Resumes the current song."""
    vc = ctx.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Resumed")
    elif not vc:
        await ctx.send("❌ Not connected to a voice channel.")


@bot.command()
async def stop(ctx):
    """Stops the song and disconnects the bot."""
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("⏹️ Stopped and left the channel")
    else:
        await ctx.send("❌ Not connected to a voice channel.")


# --- Opus Library Check (Enhanced) ---
if not discord.opus.is_loaded():
    try:
        # Change "libopus.dll" to the correct filename for your OS (e.g., 'libopus.so' on Linux)
        discord.opus.load_opus("libopus.dll")
        print("Opus library loaded successfully.")
    except Exception as e:
        # Crucial for troubleshooting: informs the developer if the Opus file is missing
        print(f"❌ ERROR: Failed to load Opus library: {e}")
        print("Please ensure 'libopus.dll' (or the correct version for your OS) is in the bot's working directory.")

# Run the Bot
if __name__ == "__main__":
    bot.run(token)
