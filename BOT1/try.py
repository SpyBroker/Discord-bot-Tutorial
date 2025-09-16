from dotenv import load_dotenv
import os

load_dotenv()
print("Loaded token:", os.getenv("DISCORD_TOKEN"))