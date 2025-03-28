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

def get_bot_token():
    """Retrieve the bot token from the parent directory."""
    try:
        # Move up one directory (outside botcode) to locate bot_token.txt
        token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_token.txt")
        with open(token_path, "r") as token_file:
            token = token_file.read().strip()  # Strip extra spaces/newlines
            return token
    except FileNotFoundError:
        logging.error(f"bot_token.txt file not found at {token_path}. Please ensure the file exists.")
        exit()  # Terminate if token file is not found
    except Exception as e:
        logging.error(f"Failed to load bot token: {e}")
        exit()

if __name__ == "__main__":
    logging.info("Starting bot...")

    # Get the bot token from the parent directory
    bot_token = get_bot_token()

    client.run(bot_token)  # Use the token to run the bot
