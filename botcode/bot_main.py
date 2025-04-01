import discord
from discord.ext import commands
import os
import logging
import asyncio
import importlib
import threading
import time
import requests
import shutil

# --------------------------
# Constants for Updater
# --------------------------
REPO_VERSION_URL = "https://raw.githubusercontent.com/Gauntbadjesse/Holly-Wood-MGMT/main/version.txt"
REPO_BOTCODE_URL = "https://github.com/Gauntbadjesse/Holly-Wood-MGMT/archive/refs/heads/main.zip"

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.DEBUG,  # Log all levels (DEBUG, INFO, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='w'  # Overwrite previous log file
)

# Adding colors to terminal output
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def color_log(level, message):
    if level == "DEBUG":
        print(f"{Color.OKBLUE}[DEBUG]{Color.ENDC} {message}")
    elif level == "INFO":
        print(f"{Color.OKGREEN}[INFO]{Color.ENDC} {message}")
    elif level == "WARNING":
        print(f"{Color.WARNING}[WARNING]{Color.ENDC} {message}")
    elif level == "ERROR":
        print(f"{Color.FAIL}[ERROR]{Color.ENDC} {message}")
    elif level == "CRITICAL":
        print(f"{Color.HEADER}[CRITICAL]{Color.ENDC} {message}")

# --------------------------
# Load the Bot Token
# --------------------------
try:
    with open("token.txt", "r") as file:
        TOKEN = file.read().strip()  # Strip spaces and newlines
        color_log("INFO", "Bot token successfully loaded.")
except FileNotFoundError:
    color_log("ERROR", "'token.txt' not found. Please create the file and add your bot token.")
    exit()

# --------------------------
# Initialize the Bot Instance
# --------------------------
intents = discord.Intents.default()
intents.message_content = True  # Required privilege for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------------
# Dynamically Load Commands (Cogs)
# --------------------------
async def load_commands():
    current_directory = os.path.dirname(__file__)  # Directory of bot_main.py (i.e. "Project/botcode")
    for file in os.listdir(current_directory):
        if file.endswith(".py") and file != os.path.basename(__file__):
            module_name = file[:-3]  # Remove '.py'
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    await module.setup(bot)  # Await module's async setup function
                    color_log("INFO", f"Loaded: {module_name}")
                else:
                    color_log("WARNING", f"Skipped: {module_name} (No setup function found)")
            except Exception as e:
                import traceback
                detailed_error = traceback.format_exc()
                logging.error(f"Failed to load {module_name}: {e}")
                color_log("ERROR", f"Failed to load: {module_name}\nDetails:\n{detailed_error}")

# --------------------------
# Updater Functionality
# --------------------------
async def check_for_updates():
    """
    Checks a remote repository for a new version.
    If an update is available, downloads and unpacks the new bot code,
    replaces files in the current botcode folder, updates the version.txt in the root,
    and returns a status message.
    """
    def run_update():
        try:
            # Fetch remote version string
            r = requests.get(REPO_VERSION_URL)
            r.raise_for_status()
            repo_version = r.text.strip()

            # Since version.txt is in the root, go one level up from botcode.
            root_dir = os.path.dirname(os.path.dirname(__file__))  # Parent of botcode
            local_version_path = os.path.join(root_dir, "version.txt")
            if not os.path.exists(local_version_path):
                return "Local version file not found in the root directory."
            with open(local_version_path, "r") as f:
                local_version = f.read().strip()

            if repo_version == local_version:
                return "Bot is already up-to-date."

            # Update available – download update ZIP
            update_zip = os.path.join(root_dir, "update.zip")
            with open(update_zip, "wb") as f:
                update_response = requests.get(REPO_BOTCODE_URL, stream=True)
                update_response.raise_for_status()
                for chunk in update_response.iter_content(chunk_size=1024):
                    f.write(chunk)

            # Extract to the root directory so that the repo structure is correct.
            extract_path = root_dir
            shutil.unpack_archive(update_zip, extract_path)

            # Assume the extracted folder is named "Holly-Wood-MGMT-main" and contains an updated "botcode" folder.
            new_botcode_path = os.path.join(extract_path, "Holly-Wood-MGMT-main", "botcode")
            current_botcode_path = os.path.dirname(__file__)  # Current botcode folder

            if not os.path.isdir(new_botcode_path):
                return "Updated botcode folder not found in the archive."

            # Replace current bot files with new versions.
            for item in os.listdir(new_botcode_path):
                src = os.path.join(new_botcode_path, item)
                dst = os.path.join(current_botcode_path, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            # Update version.txt in the root directory.
            with open(local_version_path, "w") as f:
                f.write(repo_version)

            # Clean up downloaded and extracted files.
            os.remove(update_zip)
            shutil.rmtree(os.path.join(extract_path, "Holly-Wood-MGMT-main"), ignore_errors=True)

            return "Bot has been updated successfully."
        except Exception as e:
            return f"Update failed: {e}"

    # Run the blocking update process in a separate thread.
    result = await asyncio.to_thread(run_update)
    return result

# --------------------------
# Bot Event Handlers & Commands
# --------------------------
@bot.event
async def on_ready():
    color_log("INFO", f"Bot is online! Username: {bot.user}")
    logging.info(f"Bot is online. Username: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Command Error: {error}")
    color_log("ERROR", f"An error occurred in command '{ctx.command}': {error}")
    await ctx.send(f"{Color.WARNING}An error occurred: {error}{Color.ENDC}")

@bot.command(name="update")
async def update_command(ctx):
    # Restrict this command to a specific user ID.
    allowed_user_id = 1237471534541439068
    if ctx.author.id != allowed_user_id:
        await ctx.send("You do not have permission to run this command.")
        return

    await ctx.send("Checking for updates…")
    update_status = await check_for_updates()
    await ctx.send(update_status)
    if "updated successfully" in update_status.lower():
        await ctx.send("Restarting bot now…")
        gui_restart_bot()

# --------------------------
# Main Async Function to Start the Bot
# --------------------------
async def main():
    await load_commands()  # Dynamically load commands
    try:
        color_log("INFO", "Starting bot…")
        await bot.start(TOKEN)  # Start the bot
    except discord.errors.LoginFailure:
        color_log("CRITICAL", "Error: Login failure! Please check your bot token.")
        logging.critical("Login failure! Please check your bot token.")
    except Exception as e:
        color_log("CRITICAL", f"Unexpected error occurred: {e}")
        logging.critical(f"Unexpected error: {e}")

# --------------------------
# Global Event Loop Variable for GUI Control
# --------------------------
bot_loop = None

# --------------------------
# Functions for GUI Control (Start, Stop, Restart)
# --------------------------
def run_bot():
    """Run the bot in its own event loop on a separate thread."""
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    try:
        bot_loop.run_until_complete(main())
    except Exception as e:
        color_log("ERROR", f"Bot encountered an error: {e}")
    finally:
        bot_loop.close()

def gui_start_bot():
    """Start the Discord bot from the GUI (if not already running)."""
    global bot_loop
    if not bot_loop or not bot_loop.is_running():
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        color_log("INFO", "Bot is starting from GUI…")
    else:
        color_log("WARNING", "Bot is already running.")

def gui_stop_bot():
    """Stop the bot gracefully from the GUI."""
    global bot_loop
    if bot_loop and bot_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(bot.close(), bot_loop)
        try:
            future.result()  # Wait for completion
            color_log("INFO", "Bot has been stopped from GUI.")
        except Exception as e:
            color_log("ERROR", f"Error stopping bot: {e}")
    else:
        color_log("WARNING", "Bot is not running.")

def gui_restart_bot():
    """Restart the bot from the GUI."""
    gui_stop_bot()
    time.sleep(2)  # Pause briefly before restarting
    gui_start_bot()

# --------------------------
# If Run Directly, Start the Bot (for testing)
# --------------------------
if __name__ == "__main__":
    run_bot()
