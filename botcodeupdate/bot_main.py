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
# These constants define where in your GitHub repo the updated folder resides.
REPO_OWNER = "Gauntbadjesse"
REPO_NAME = "Holly-Wood-MGMT"
REPO_FOLDER = "botcode"  # The folder in your GitHub repo to download

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.DEBUG,  # Log all levels (DEBUG, INFO, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='w'  # Overwrite any previous log file
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
    current_directory = os.path.dirname(__file__)  # Directory of bot_main.py (i.e. Project/botcode)
    for file in os.listdir(current_directory):
        if file.endswith(".py") and file != os.path.basename(__file__):
            module_name = file[:-3]  # Remove .py
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
# Helper: Download a GitHub Folder Recursively
# --------------------------
def download_github_folder(repo_owner, repo_name, folder_path, dest_dir, branch="main"):
    """
    Recursively downloads files and directories from a GitHub folder using the GitHub API.
    - repo_owner: The owner of the repository.
    - repo_name: The repository name.
    - folder_path: Path inside the repo (e.g., "botcode").
    - dest_dir: The destination directory on local disk.
    - branch: Branch to download from.
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
    Checks GitHub for a new version. If a new version is available, it downloads the entire updated
    botcode folder (using the GitHub API) into a temporary folder in the project root, deletes the old
    botcode folder, renames the new folder to "botcode", restores token.txt if available, and updates
    version.txt in the root.
    """
    def run_update():
        try:
            # Fetch remote version string.
            r = requests.get(REPO_VERSION_URL)
            r.raise_for_status()
            repo_version = r.text.strip()

            # Get the root directory (one level above botcode).
            current_dir = os.path.dirname(__file__)  # This is botcode folder.
            root_dir = os.path.dirname(current_dir)    # This is the project root.
            local_version_path = os.path.join(root_dir, "version.txt")
            if not os.path.exists(local_version_path):
                return "Local version file not found in the root directory."
            with open(local_version_path, "r") as f:
                local_version = f.read().strip()

            if repo_version == local_version:
                return "Bot is already up-to-date."

            # Define temporary folder for the new botcode.
            new_botcode_temp = os.path.join(root_dir, "botcode_temp")
            if os.path.exists(new_botcode_temp):
                shutil.rmtree(new_botcode_temp)

            # Download the updated botcode folder from GitHub into the temporary folder.
            download_github_folder(REPO_OWNER, REPO_NAME, REPO_FOLDER, new_botcode_temp, branch="main")

            # (Optional) Preserve token.txt from the current botcode.
            token_file = os.path.join(current_dir, "token.txt")
            token_content = None
            if os.path.exists(token_file):
                with open(token_file, "r") as tf:
                    token_content = tf.read()

            # Rename (or delete) the old botcode folder.
            # Because this updater is running from within botcode, you cannot delete the folder you're in.
            # So, we move the current botcode folder to a backup name.
            backup_botcode = os.path.join(root_dir, "botcode_old")
            if os.path.exists(backup_botcode):
                shutil.rmtree(backup_botcode)
            os.rename(current_dir, backup_botcode)

            # Rename the newly downloaded folder to "botcode" in the root.
            new_botcode_final = os.path.join(root_dir, "botcode")
            os.rename(new_botcode_temp, new_botcode_final)

            # Restore token.txt if it was preserved.
            if token_content:
                new_token_path = os.path.join(new_botcode_final, "token.txt")
                with open(new_token_path, "w") as tf:
                    tf.write(token_content)

            # Delete the backup folder.
            shutil.rmtree(backup_botcode, ignore_errors=True)

            # Update the local version file.
            with open(local_version_path, "w") as f:
                f.write(repo_version)

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
    await load_commands()  # Dynamically load commands/cogs
    try:
        color_log("INFO", "Starting bot…")
        await bot.start(TOKEN)  # Start the bot using your token
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
    time.sleep(2)  # Brief pause before restarting
    gui_start_bot()

# --------------------------
# If Run Directly, Start the Bot (for testing purposes)
# --------------------------
if __name__ == "__main__":
    run_bot()
