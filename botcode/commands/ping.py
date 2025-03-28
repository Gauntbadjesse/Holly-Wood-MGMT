import discord
from discord.ext import commands
import psutil
from datetime import datetime
import logging  # Add logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ping_command.log"),  # Create a dedicated log file for ping
        logging.StreamHandler()  # Log to console for debugging
    ]
)

class Ping(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        # Log command usage
        logging.info(f"'!ping' command triggered by {ctx.author} in channel #{ctx.channel} (Guild: {ctx.guild})")

        try:
            # Calculate bot latency
            latency_ms = round(self.client.latency * 1000, 2)

            # Fetch CPU and memory stats
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = round(memory_info.used / (1024 ** 2), 2)  # MB
            memory_total = round(memory_info.total / (1024 ** 2), 2)  # MB
            memory_percent = memory_info.percent

            # Calculate uptime
            bot_start_time = datetime.fromtimestamp(psutil.Process().create_time())
            current_time = datetime.utcnow()
            uptime = str(current_time - bot_start_time).split(".")[0]  # Format: HH:MM:SS

            # Construct embed message
            embed = discord.Embed(
                title="Bot Status Report",
                description="Detailed technical stats for the bot",
                color=0x00FF00  # Green
            )
            embed.add_field(name="Latency", value=f"{latency_ms} ms", inline=False)
            embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=False)
            embed.add_field(name="Memory Usage", value=f"{memory_usage} MB / {memory_total} MB ({memory_percent}%)", inline=False)
            embed.add_field(name="Uptime", value=uptime, inline=False)

            # Send embed message
            await ctx.send(embed=embed)

            # Log successful execution
            logging.info("'!ping' command executed successfully")

        except Exception as e:
            # Log errors if the command fails
            logging.error(f"Error in '!ping' command: {e}")
            await ctx.send(f"An error occurred while processing the '!ping' command: {e}")

# Setup function for adding the cog
async def setup(client):
    await client.add_cog(Ping(client))
