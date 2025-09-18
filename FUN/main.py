import os
import logging
from dotenv import load_dotenv
import random
import asyncio
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

scores = {}

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and ready!")

def ensure_score(user_id):
    if user_id not in scores:
        scores[user_id] = {"wins": 0, "losses": 0, "ties": 0}

@bot.command()
async def coinflip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"🪙 The coin landed on **{result}**!")

@bot.command()
async def rps(ctx, choice: str):
    options = ["rock", "paper", "scissors"]
    choice = choice.lower()
    if choice not in options:
        await ctx.send("❌ Please choose rock, paper, or scissors. Example: `!rps rock`")
        return

    bot_choice = random.choice(options)

    if choice == bot_choice:
        result = "tie"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "win"
    else:
        result = "lose"

    ensure_score(ctx.author.id)
    if result == "win":
        scores[ctx.author.id]["wins"] += 1
    elif result == "lose":
        scores[ctx.author.id]["losses"] += 1
    else:
        scores[ctx.author.id]["ties"] += 1

    emoji = {"win":"🎉 You win!", "lose":"😢 I win!", "tie":"🤝 It's a tie!"}
    await ctx.send(f"You chose **{choice}**. I chose **{bot_choice}**. {emoji[result]}")

@bot.command()
async def guess(ctx, low: int = 1, high: int = 10):
    if low >= high:
        await ctx.send("⚠️ Invalid range. Make sure low < high. Example: `!guess 1 20`")
        return

    number = random.randint(low, high)
    attempts = 5
    await ctx.send(f"🔢 I'm thinking of a number between {low} and {high}. You have {attempts} tries. Type your guess!")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    for _ in range(attempts):
        try:
            msg = await bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f"⏲️ Time's up! The number was **{number}**.")
            return

        guess_num = int(msg.content)
        if guess_num == number:
            await ctx.send("🎉 Correct! You guessed the number!")
            return
        elif guess_num < number:
            await ctx.send("🔺 Higher!")
        else:
            await ctx.send("🔻 Lower!")

    await ctx.send(f"❌ Out of attempts! The number was **{number}**.")

@bot.command()
async def score(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = member.id
    ensure_score(uid)
    s = scores[uid]
    await ctx.send(f"📊 {member.display_name} — Wins: {s['wins']}, Losses: {s['losses']}, Ties: {s['ties']}")

@bot.command()
@commands.has_permissions(administrator=True)
async def reset_scores(ctx):
    scores.clear()
    await ctx.send("✅ All scores have been reset.")

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)