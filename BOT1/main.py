import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import asyncio
import datetime

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
scores = {}


secret_role = "Gamer"

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}" )

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title ="🤖 Chat Buddy Bot",
        description="I can tell jokes, roll dice, and more!",
        color=discord.Color.blue()
    )
    embed.add_field(name="!joke", value="Tells a random joke.", inline=False)
    embed.add_field(name="!roll", value="Rolls a dice 🎲", inline=False)
    embed.add_field(name="!info", value="Shows this help box 📘", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def roll(ctx):
    number = random.randint(1, 6)
    await ctx.send(f"🎲 You rolled a {number}!")

@bot.command()
async def joke(ctx):
    jokes = [
        "Why did the scarecrow win an award? Because he was outstanding in his field! 🌾",
        "Why don’t scientists trust atoms? Because they make up everything! ⚛️",
        "Why was the math book sad? Because it had too many problems. 📘"
    ]
    await ctx.send(random.choice(jokes))

# !hello
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} is now removed from {secret_role}")
    else:
        await ctx.send("Role doesn't exist")

# !dm (Hello World)msg
@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

@bot.command()
async def poll(ctx,*,question):
    embed = discord.Embed(title = "New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")


@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club!")

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You don't have permission to do that!")


@bot.command()
async def remindme(ctx,seconds:int,*,task:str):
    await ctx.send(f"⏰ Okay! I’ll remind you in {seconds} seconds to: **{task}**")
    await asyncio.sleep(seconds)
    await ctx.send(f"🔔 Reminder: {ctx.author.mention}, don’t forget to {task}!")

@bot.command()
async def userinfo(ctx,member:discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(
        title=f"User Info - {member}",
        color=discord.Color.green(),
        timestamp = datetime.datetime.now()
    )
    embed.add_field(name="👤 Username", value=member.name, inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Joined Discord", value=member.created_at.strftime("%Y-%m-%d"), inline=False)
    embed.add_field(name="📅 Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

bad_words = ["stupid", "dumb", "idiot", "shit"]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return # dont delete bot's own message

    for word in bad_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"⚠️ Watch your language, {message.author.mention}!")
            return
    await bot.process_commands(message) # lets other commands still work

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member:discord.Member, *, reason="No reason given"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.name} was kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member:discord.Member,*,reason="No reason given"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.name} was banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member:discord.Member, seconds: int,*, reason="No reason given"):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")

    # if role doesn’t exist, create one
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)

    await member.add_roles(mute_role,reason=reason)
    await ctx.send(f"🔇 {member.mention} has been muted for {seconds} seconds. Reason: {reason}")

    await asyncio.sleep(seconds)
    await member.remove_roles(mute_role)
    await ctx.send(f"🔊 {member.mention} is now unmuted.")

def ensure_score(user_id):
    if user_id not in scores:
        scores[user_id] = {"wins": 0, "losses": 0, "ties": 0}


@bot.command()
async def coinflip(ctx):
    result = random.choice(["Heads", "Tails"])
    await ctx.send(f"🪙 The coin landed on **{result}**!")

@bot.command()
async def rps(ctx, choice:str):
    options = [ "rock", "paper", "scissors"]
    choice = choice.lower()
    if choice not in options:
        await ctx.send("❌ Please choose rock, paper, or scissors. Example: `!rps rock`")
        return
    bot_choice = random.choice(options)

    #decide result
    if choice == bot_choice:
        result = "tie"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "win"
    else:
        result = "lose"

    # update scoreboard
    ensure_score(ctx.author.id)
    if result == "win":
        scores[ctx.author.id]["wins"] += 1
    elif result == "lose":
        scores[ctx.author.id]["losses"] += 1
    else:
        scores[ctx.author.id]["ties"] += 1

    # friendly message
    emoji = {"win": "🎉 You win!", "lose": "😢 I win!", "tie": "🤝 It's a tie!"}
    await ctx.send(f"You chose **{choice}**. I chose **{bot_choice}**. {emoji[result]}")

@bot.command()
async def guess(ctx,low:int=1, high: int=10):
    if low > high:
        await ctx.send(f"⚠️ Invalid range. Make sure low < high. Example: `!guess 1 20`")
        return

    number = random.randint(low,high)
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
async def score(ctx, member:discord.Member = None ):
    member = member or ctx.author
    uid = member.id
    ensure_score(uid)
    s=scores[uid]
    await ctx.send(f"📊 {member.display_name} — Wins: {s['wins']}, Losses: {s['losses']}, Ties: {s['ties']}")

@bot.command()
@commands.has_permissions(administrator=True)
async def reset_scores(ctx):
    scores.clear()
    await ctx.send("✅ All scores have been reset.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)