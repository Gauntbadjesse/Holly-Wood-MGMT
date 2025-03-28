import os
import discord
from discord.ext import commands
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Enable Message Content Intent
client = commands.Bot(command_prefix="!", intents=intents)

# Function to load extensions from a specific folder
async def load_extensions(folder_name):
    folder_path = os.path.join(os.path.dirname(__file__), folder_name)
    if not os.path.exists(folder_path):
        logging.warning(f"The folder '{folder_name}' does not exist. Skipping...")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith(".py"):
            module = f"{folder_name}.{filename[:-3]}"  # Strip .py extension
            try:
                if module not in client.extensions:  # Check if module is already loaded
                    await client.load_extension(module)  # Load the module
                    logging.info(f"Loaded module: {module}")
                else:
                    logging.warning(f"Module '{module}' is already loaded. Skipping...")
            except Exception as e:
                logging.error(f"Failed to load module {module}: {e}")

# Function to load all extensions (commands, embeds, and database)
async def load_all_extensions():
    await load_extensions("commands")   # Load command modules
    await load_extensions("embeds")     # Load embed modules
    await load_extensions("database")   # Load database modules

@client.event
async def on_ready():
    logging.info(f"Bot logged in as {client.user}")
    logging.info("Bot is ready and connected to the server.")
    await load_all_extensions()  # Load all extensions on startup

if __name__ == "__main__":
    logging.info("Starting bot...")

    client.run("MTM1MDY1MTYyNzAyMjg0ODEwNQ.GByK6B.ATPGToeD2d7l9iynO43SxbH5a0-1VGfAlpS68g")  # Replace with your actual bot token
