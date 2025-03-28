import discord
from discord.ext import commands
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("unregister_log.log"),
        logging.StreamHandler()
    ]
)

class Unregister(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def unregister(self, ctx):
        """Unregister all slash commands (/commands) from the bot."""
        try:
            # Go through all registered slash commands and remove them
            commands_to_remove = [cmd.name for cmd in self.client.tree.commands]
            for cmd_name in commands_to_remove:
                self.client.tree.remove_command(cmd_name)

            # Sync the bot's command tree to ensure changes are applied
            await self.client.tree.sync()

            # Notify the user in Discord and log success
            await ctx.send("All slash commands have been unregistered successfully.")
            logging.info("All slash commands have been unregistered.")
        except Exception as e:
            logging.error(f"Error unregistering slash commands: {e}")
            await ctx.send(f"Failed to unregister slash commands: {e}")

# Setup function for adding the cog
async def setup(client):
    await client.add_cog(Unregister(client))
    logging.info("Unregister Cog loaded successfully.")
