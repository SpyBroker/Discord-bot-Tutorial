import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp


load_dotenv()
Token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command(name= "joke")
async def joke(ctx):
    url = "https://v2.jokeapi.dev/joke/Any"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            json_data = await response.json()

    try:
        # Check the type of joke returned
        if json_data.get("type") == "single":
            j = json_data.get("joke")
        elif json_data.get("type") == "twopart":
            j = f"{json_data.get('setup')}\n{json_data.get('delivery')}"
        else:
            j = "Oops! Couldn't fetch a joke this time."
    except KeyError:
        if "error" in json_data and json_data["error"]:
            j = "The joke API had an issue, try again later!"

    await ctx.send(j)


bot.run(Token)