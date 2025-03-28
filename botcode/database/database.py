import discord
from discord.ext import commands
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("moderation_log.log"),
        logging.StreamHandler()
    ]
)

ALLOWED_ROLE_ID = [1342610409525608479, 1342610501305372794]  # Replace with your actual moderator role IDs
ALLOWED_USER_ID = 1237471534541439068  # Replace with your actual user ID

intents = discord.Intents.default()
intents.members = True  # Enable the members intent for accessing full member lists

class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.connection_string = "mongodb+srv://jessebutler2007:Owls213572@cluster0.gtrwy.mongodb.net/?retryWrites=true&w=majority&tls=true"
        self.db_name = "moderation_db"
        self.logs_collection_name = "moderation_logs"
        self.database = None
        self.connect_to_database()

    def connect_to_database(self):
        try:
            client = MongoClient(self.connection_string)
            self.database = client[self.db_name]
            if self.logs_collection_name not in self.database.list_collection_names():
                self.database[self.logs_collection_name].insert_one({"case_number": 0})
            logging.info("Connected to MongoDB successfully!")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")

    async def has_permission(self, source) -> bool:
        """
        Check if the user has the required role or user ID.
        Accepts both `ctx` (text commands) and `interaction` (slash commands).
        """
        user = source.author if isinstance(source, commands.Context) else source.user
        allowed_roles = [role.id for role in user.roles]
        return any(role in allowed_roles for role in ALLOWED_ROLE_ID) or user.id == ALLOWED_USER_ID

    async def dm_user(self, user: discord.User, message: str):
        """Send a DM to the user with the given message."""
        try:
            await user.send(message)
        except discord.Forbidden:
            logging.warning(f"Unable to send DM to {user}.")

    @commands.command(name="ban")
    async def ban(self, ctx, user: discord.Member, *, reason: str):
        """Text command to ban a user."""
        await ctx.message.delete()  # Deletes the sender's command message
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

        await self.dm_user(user, f"You have been banned from the server by {ctx.author}. Reason: {reason}.")
        await ctx.send(f"{user.mention} has been banned for: {reason}.")

    @commands.command(name="warn")
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """Text command to warn a user."""
        await ctx.message.delete()  # Deletes the sender's command message
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

        await self.dm_user(user, f"You have been warned by {ctx.author}. Reason: {reason}.")
        await ctx.send(f"{user.mention} has been warned for: {reason}.")

    @commands.command(name="mute")
    async def mute(self, ctx, user: discord.Member, duration: int, *, reason: str):
        """Text command to mute a user."""
        await ctx.message.delete()  # Deletes the sender's command message
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

        await self.dm_user(user, f"You have been muted for {duration} minutes by {ctx.author}. Reason: {reason}.")
        await ctx.send(f"{user.mention} has been muted for {duration} minutes for: {reason}.")

    @commands.command(name="logs")
    async def logs(self, ctx, user: discord.Member):
        """Text command to view moderation logs for a specific user."""
        await ctx.message.delete()  # Deletes the sender's command message
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        logs_cursor = self.database[self.logs_collection_name].find({"user_id": user.id}).sort("case_number", 1)
        logs = list(logs_cursor)

        if not logs:
            await ctx.send(f"No logs found for {user.mention}.")
            return

        embed = discord.Embed(
            title=f"Moderation Logs: {user.display_name}",
            description="Here are the moderation actions for the selected user.",
            color=discord.Color.blue()
        )

        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp'])
            formatted_timestamp = timestamp.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')

            embed.add_field(
                name=f"Case #{log['case_number']}",
                value=(
                    f"**Action:** {log['action_type']}\n"
                    f"**Reason:** {log.get('reason', 'No reason provided')}\n"
                    f"**Timestamp:** {formatted_timestamp}"
                ),
                inline=False
            )

        embed.set_footer(text="Logs generated for moderation purposes.")
        await ctx.send(embed=embed)

    @commands.command(name="pardon")
    async def pardon(self, ctx, user: discord.Member):
        """Command to pardon a user's specific moderation record."""
        await ctx.message.delete()  # Deletes the sender's command message
        if not await self.has_permission(ctx):
            await ctx.send("You do not have permission to use this command.")
            return

        # Fetch all moderation logs for the user
        logs = list(self.database[self.logs_collection_name].find({"user_id": user.id}).sort("case_number", 1))
        if not logs:
            await ctx.send(f"No moderation logs found for {user.mention}.")
            return

        # Display the logs to the moderator
        log_list = "\n".join(
            [f"{idx + 1}. **Action:** {log['action_type']} | **Reason:** {log.get('reason', 'No reason provided')} | **Case #:** {log['case_number']}" 
             for idx, log in enumerate(logs)]
        )
        await ctx.send(f"Moderation Logs for {user.mention}:\n{log_list}")

        # Wait for the moderator to respond with the log number to pardon
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            response = await self.client.wait_for("message", check=check, timeout=60)
            selected_idx = int(response.content) - 1
            if 0 <= selected_idx < len(logs):
                # Remove the selected log from the database
                case_to_remove = logs[selected_idx]
                self.database[self.logs_collection_name].delete_one({"_id": case_to_remove["_id"]})
                await ctx.send(f"Successfully pardoned case #{case_to_remove['case_number']} for {user.mention}.")
            else:
                await ctx.send("Invalid selection. No changes were made.")
        except TimeoutError:
            await ctx.send("You took too long to respond. No changes were made.")

# Setup function for adding the cog
async def setup(client):
    moderation = Moderation(client)
    await client.add_cog(moderation)
