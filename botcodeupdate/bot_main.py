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
# Global Bot Status
# --------------------------
bot_current_status = "Offline"  # Shared variable for status ("Offline", "Starting", "Online")

# --------------------------
# Constants for Updater
# --------------------------
REPO_VERSION_URL = "https://raw.githubusercontent.com/Gauntbadjesse/Holly-Wood-MGMT/main/version.txt"
# Repository details. In your GitHub repo, rename the folder that contains your updated code to "botcodeupdate".
REPO_OWNER = "Gauntbadjesse"
REPO_NAME = "Holly-Wood-MGMT"
REPO_FOLDER = "botcodeupdate"

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.DEBUG,  # Log all levels (DEBUG, INFO, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='w'  # Overwrite log file
)

# Terminal colors for log output
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
        TOKEN = file.read().strip()
        color_log("INFO", "Bot token successfully loaded.")
except FileNotFoundError:
    color_log("ERROR", "'token.txt' not found. Please create the file and add your bot token.")
    exit()

# --------------------------
# Initialize the Bot Instance
# --------------------------
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# --------------------------
# Dynamically Load Commands (Cogs)
# --------------------------
async def load_commands():
    current_directory = os.path.dirname(__file__)  # This is the botcode folder.
    for file in os.listdir(current_directory):
        if file.endswith(".py") and file != os.path.basename(__file__):
            module_name = file[:-3]  # Remove .py extension.
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    await module.setup(bot)
                    color_log("INFO", f"Loaded: {module_name}")
                else:
                    color_log("WARNING", f"Skipped: {module_name} (No setup function found)")
            except Exception as e:
                import traceback
                detailed_error = traceback.format_exc()
                logging.error(f"Failed to load {module_name}: {e}")
                color_log("ERROR", f"Failed to load: {module_name}\nDetails:\n{detailed_error}")

# --------------------------
# Helper: Download GitHub Folder
# --------------------------
def download_github_folder(repo_owner, repo_name, folder_path, dest_dir, branch="main"):
    """
    Recursively downloads files/directories from GitHub using the API.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{folder_path}?ref={branch}"
    response = requests.get(url)
    response.raise_for_status()
    items = response.json()
    for item in items:
        destination_path = os.path.join(dest_dir, item["name"])
        if item["type"] == "dir":
            os.makedirs(destination_path, exist_ok=True)
            download_github_folder(repo_owner, repo_name, item["path"], destination_path, branch)
        elif item["type"] == "file":
            file_url = item["download_url"]
            r = requests.get(file_url)
            r.raise_for_status()
            with open(destination_path, "wb") as f:
                f.write(r.content)

# --------------------------
# Updater Functionality
# --------------------------
async def check_for_updates():
    """
    Checks for a new version on GitHub. If found, it downloads the updated folder (named "botcodeupdate")
    into a temporary folder, backs up the current "botcode", renames the new folder to "botcode",
    restores token.txt if it was preserved, and updates version.txt in the root.
    """
    def run_update():
        try:
            # Fetch remote version.
            r = requests.get(REPO_VERSION_URL)
            r.raise_for_status()
            repo_version = r.text.strip()

            # Determine the project root (one level above the current botcode folder).
            current_botcode_dir = os.path.dirname(__file__)
            root_dir = os.path.dirname(current_botcode_dir)
            local_version_path = os.path.join(root_dir, "version.txt")
            if not os.path.exists(local_version_path):
                return "Local version file not found in the root directory."
            with open(local_version_path, "r") as f:
                local_version = f.read().strip()

            if repo_version == local_version:
                return "Bot is already up-to-date."

            # Prepare a temporary folder for the update.
            temp_folder = os.path.join(root_dir, "botcode_temp")
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            os.makedirs(temp_folder, exist_ok=True)

            # Download updated folder from GitHub (named "botcodeupdate") into temp_folder.
            download_github_folder(REPO_OWNER, REPO_NAME, REPO_FOLDER, temp_folder, branch="main")

            # Preserve token.txt if it exists.
            token_file = os.path.join(current_botcode_dir, "token.txt")
            token_content = None
            if os.path.exists(token_file):
                with open(token_file, "r") as tf:
                    token_content = tf.read()

            # Backup old botcode folder.
            backup_botcode = os.path.join(root_dir, "botcode_old")
            if os.path.exists(backup_botcode):
                shutil.rmtree(backup_botcode)
            os.rename(current_botcode_dir, backup_botcode)

            # Rename the downloaded temp folder to "botcode".
            new_botcode = os.path.join(root_dir, "botcode")
            os.rename(temp_folder, new_botcode)

            # Restore token.txt if preserved.
            if token_content:
                new_token_path = os.path.join(new_botcode, "token.txt")
                with open(new_token_path, "w") as tf:
                    tf.write(token_content)

            # Remove the backup folder.
            shutil.rmtree(backup_botcode, ignore_errors=True)

            # Update the local version file.
            with open(local_version_path, "w") as f:
                f.write(repo_version)

            return "Bot has been updated successfully."
        except Exception as e:
            return f"Update failed: {e}"

    result = await asyncio.to_thread(run_update)
    return result

# --------------------------
# Bot Event Handlers & Commands
# --------------------------
@bot.event
async def on_ready():
    global bot_current_status
    bot_current_status = "Online"
    color_log("INFO", f"Bot is online! Username: {bot.user}")
    logging.info(f"Bot is online. Username: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Command Error: {error}")
    color_log("ERROR", f"An error occurred in command '{ctx.command}': {error}")
    await ctx.send(f"{Color.WARNING}An error occurred: {error}{Color.ENDC}")

@bot.command(name="update")
async def update_command(ctx):
    # Restrict the command to a specific user ID.
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
    await load_commands()
    try:
        color_log("INFO", "Starting bot…")
        await bot.start(TOKEN)
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
    global bot_loop, bot_current_status
    bot_current_status = "Starting"
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
    global bot_loop, bot_current_status
    if not bot_loop or not bot_loop.is_running():
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        color_log("INFO", "Bot is starting from GUI…")
    else:
        color_log("WARNING", "Bot is already running.")

def gui_stop_bot():
    """Stop the bot gracefully from the GUI."""
    global bot_loop, bot_current_status
    if bot_loop and bot_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(bot.close(), bot_loop)
        try:
            future.result()  # Wait for completion.
            bot_current_status = "Offline"
            color_log("INFO", "Bot has been stopped from GUI.")
        except Exception as e:
            color_log("ERROR", f"Error stopping bot: {e}")
    else:
        color_log("WARNING", "Bot is not running.")

def gui_restart_bot():
    """Restart the bot from the GUI."""
    gui_stop_bot()
    time.sleep(2)
    gui_start_bot()

# --------------------------
# If Run Directly, Start the Bot (For Testing)
# --------------------------
if __name__ == "__main__":
    run_bot()
