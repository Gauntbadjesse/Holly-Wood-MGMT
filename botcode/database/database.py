import os
import logging
from pymongo import MongoClient
from discord.ext import commands
from datetime import datetime, timedelta
import discord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("moderation_log.log"),
        logging.StreamHandler()
    ]
)

ALLOWED_ROLE_ID = [1342610409525608479, 1342610501305372794]  # Replace with actual moderator role IDs
ALLOWED_USER_ID = 1237471534541439068  # Replace with your actual user ID

class Moderation(commands.Cog):  # Ensure it inherits from commands.Cog
    def __init__(self, client):
        self.client = client
        self.connection_string = None
        self.db_name = None
        self.logs_collection_name = None
        self.database = None
        self.load_db_config()
        self.connect_to_database()

    def load_db_config(self):
        """Load MongoDB configuration from the db.txt file."""
        try:
            db_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db.txt")
            with open(db_config_path, "r") as file:
                config = {}
                for line in file:
                    key, value = line.strip().split("=", 1)
                    config[key] = value
                self.connection_string = config.get("connection_string")
                self.db_name = config.get("db_name")
                self.logs_collection_name = config.get("logs_collection_name")
            logging.info("Database configuration loaded successfully.")
        except FileNotFoundError:
            logging.error(f"db.txt file not found at {db_config_path}. Please ensure the file exists.")
            exit()
        except Exception as e:
            logging.error(f"Failed to load database configuration: {e}")
            exit()

    def connect_to_database(self):
        """Connect to MongoDB using the loaded configuration."""
        try:
            client = MongoClient(self.connection_string)
            self.database = client[self.db_name]
            if self.logs_collection_name not in self.database.list_collection_names():
                self.database[self.logs_collection_name].insert_one({"case_number": 0})
            logging.info("Connected to MongoDB successfully!")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            exit()

    async def has_permission(self, source) -> bool:
        """Check if the user has the required role or user ID."""
        user = source.author if isinstance(source, commands.Context) else source.user
        allowed_roles = [role.id for role in user.roles]
        return any(role in allowed_roles for role in ALLOWED_ROLE_ID) or user.id == ALLOWED_USER_ID

    async def dm_user(self, user: discord.User, embed: discord.Embed):
        """Send a DM to the user with the given embed."""
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            logging.warning(f"Unable to send DM to {user}.")

    @commands.command(name="ban")
    async def ban(self, ctx, user: discord.Member, *, reason: str):
        """Command to ban a user."""
        await ctx.message.delete()
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        await user.ban(reason=reason)
        self.database[self.logs_collection_name].insert_one({
            "case_number": self.database[self.logs_collection_name].count_documents({}) + 1,
            "username": user.display_name,
            "user_id": user.id,
            "mention": user.mention,
            "action_type": "Ban",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        embed = discord.Embed(
            title="🚫 **Ban Notice**",
            description=(
                f"Dear {user.display_name},\n\n"
                f"You have been banned from **Hollywood Management**.\n\n"
                f"**Reason:** {reason}\n\n"
                "For further inquiries, contact server administration."
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="This action has been logged by Hollywood Management.", icon_url="https://example.com/icon.png")
        await self.dm_user(user, embed)
        await ctx.send(f"{user.mention} has been banned for: {reason}")

    @commands.command(name="warn")
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Command to warn a user."""
        await ctx.message.delete()
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        self.database[self.logs_collection_name].insert_one({
            "case_number": self.database[self.logs_collection_name].count_documents({}) + 1,
            "username": user.display_name,
            "user_id": user.id,
            "mention": user.mention,
            "action_type": "Warn",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        embed = discord.Embed(
            title="⚠️ **Warning Notice**",
            description=(
                f"Dear {user.display_name},\n\n"
                f"You have been issued a **warning**.\n\n"
                f"**Reason:** {reason}\n\n"
                "Please adhere to the server guidelines to avoid further action."
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="This action has been logged by Hollywood Management.", icon_url="https://example.com/icon.png")
        await self.dm_user(user, embed)
        await ctx.send(f"{user.mention} has been warned for: {reason}")

    @commands.command(name="mute")
    async def mute(self, ctx, user: discord.Member, duration: int, *, reason: str):
        """Command to mute a user."""
        await ctx.message.delete()
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        if duration <= 0:
            await ctx.send("Invalid duration specified. Must be greater than 0 minutes.")
            return

        timeout_until = discord.utils.utcnow() + timedelta(minutes=duration)
        await user.timeout(timeout_until, reason=f"Muted by {ctx.author} for: {reason}")

        self.database[self.logs_collection_name].insert_one({
            "case_number": self.database[self.logs_collection_name].count_documents({}) + 1,
            "username": user.display_name,
            "user_id": user.id,
            "mention": user.mention,
            "action_type": "Mute",
            "duration": duration,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        embed = discord.Embed(
            title="🔇 **Mute Notice**",
            description=(
                f"Dear {user.display_name},\n\n"
                f"You have been muted in **Hollywood Management**.\n\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** {duration} minutes\n\n"
                "Please use this time to reflect and rejoin the server constructively."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="This action has been logged by Hollywood Management.", icon_url="https://example.com/icon.png")
        await self.dm_user(user, embed)
        await ctx.send(f"{user.mention} has been muted for {duration} minutes for: {reason}")

    @commands.command(name="logs")
    async def logs(self, ctx, user: discord.Member):
        """Command to view moderation logs for a user."""
        await ctx.message.delete()
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        logs_cursor = self.database[self.logs_collection_name].find({"user_id": user.id}).sort("case_number", 1)
        logs = list(logs_cursor)

        if not logs:
            await ctx.send(f"No logs found for {user.mention}.")
            return

        embed = discord.Embed(
            title=f"📝 **Moderation Logs for {user.display_name}**",
            description="Below are the logged moderation actions for this user.",
            color=discord.Color.green()
        )

        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp'])
            formatted_timestamp = timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
            embed.add_field(
                name=f"Case #{log['case_number']}",
                value=f"**Action:** {log['action_type']}\n**Reason:** {log.get('reason', 'No reason provided')}\n**Timestamp:** {formatted_timestamp}",
                inline=False
            )

        embed.set_footer(text="Logs generated by Hollywood Management.", icon_url="https://example.com/icon.png")
        await ctx.send(embed=embed)

async def setup(client):
    moderation = Moderation(client)
    await client.add_cog(moderation)
