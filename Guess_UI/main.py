import discord
import os
import random
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from discord.ui import View, Button, Modal, TextInput

load_dotenv()
Token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
active_games = {}

pre_game_messages = [
    "Get ready to guess!",
    "Let's see if you can guess the number!",
    "The guessing game is about to begin!"
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


class RangeInputModel(Modal):
    def __init__(self, ctx):
        super().__init__(title ="Set Game Range")
        self.ctx = ctx
        self.range_input = TextInput(label="Enter the maximum range", placeholder="e.g., 100")
        self.add_item(self.range_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_range = int(self.range_input.value)
            if max_range < 1:
                await interaction.response.send_message("Please enter a number greater than 1.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ehemeral=True)
            return

        secret_number = random.randint(1, max_range)
        active_games[self.ctx.author.id] = {
            "secret_number": secret_number,
            "attempts":0
        }
        await interaction.response.send_message(
            f"Game started! I'm thinking of a number between 1 and {max_range}. Start guessing with `!guess <your number>`."
        )


class StartGameView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: discord.Interaction, button: Button):
        if self.ctx.author.id in active_games:
            await interaction.response.send_message(
                "You already have an active game! Finish it before starting a new one.",
                ephemeral=True
            )
            return
        modal = RangeInputModel(self.ctx)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button:Button):
        await interaction.response.send_message("Game setup canceled.", ephemeral=True)


@bot.command(name="startGuess")
async def start_guess_ui(ctx, pre_game_messages=pre_game_messages):
    pre_game_messages = random.choice(pre_game_messages)
    await ctx.send(pre_game_messages)

    view = StartGameView(ctx)
    await ctx.send("Ready to start the game?", view=view)


async def joke():
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

    return j



@bot.command(name="guess")
async def guess(ctx,user_guess: int):
    game = active_games.get(ctx.author.id)

    if game:
        game["attempts"] += 1
        secret_number = game["secret_number"]

        if user_guess < secret_number:
            await ctx.send("You guessed too low!")
        elif user_guess > secret_number:
            await ctx.send("You guessed too high!")
        else:
            attempts = game["attempts"]

            joke_text = await joke()

            await ctx.send(f'🎉Congrats {ctx.author.mention}! You guessed the number {secret_number} in {attempts} tries! ')
            await ctx.send(f'Here is a dark joke for you : {joke_text}')

            del active_games[ctx.author.id]

    else:
        await ctx.send(f"{ctx.author.mention}, you haven't started a game yes! Type `!startGuess`to begin.")

bot.run(Token)