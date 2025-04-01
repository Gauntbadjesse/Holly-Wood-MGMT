import discord
from discord.ext import commands
import sqlite3
import logging
import re
from datetime import timedelta

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("moderation.log"),
        logging.StreamHandler()
    ]
)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Connect to moderation.db (it will be created if it doesn't exist)
        self.db = sqlite3.connect("moderation.db")
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        # Create table if it doesn't exist
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                reason TEXT,
                moderator_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        )
        self.db.commit()

    def log_action(self, user_id, action, reason, moderator_id):
        # Insert a new log entry into the database
        self.cursor.execute(
            "INSERT INTO logs (user_id, action, reason, moderator_id) VALUES (?, ?, ?, ?)",
            (str(user_id), action, reason, str(moderator_id))
        )
        self.db.commit()

    async def dm_user(self, user: discord.Member, message: str):
        # Attempt to DM the user; log an error if it fails
        try:
            await user.send(message)
        except Exception as e:
            logging.error(f"Could not DM user {user.id}: {e}")

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """
        Warn a user. Usage: !warn @user <reason>
        """
        # Only allowed for moderators with role ID 1342611104249024512
        if not any(role.id == 1342611104249024512 for role in ctx.author.roles):
            return await ctx.send("You don't have permission to use this command.", delete_after=10)
        try:
            self.log_action(member.id, "WARN", reason, ctx.author.id)
            await self.dm_user(member, f"You have been warned for: {reason}")
            await ctx.send(f"{member.mention} has been warned for: {reason}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def mute(self, ctx, member: discord.Member, time: str, *, reason: str):
        """
        Mute a user using Discord's timeout feature. Usage: !mute @user <time> <reason>
        Time should be in the format (e.g., 10s, 5m, 2h, 1d)
        """
        if not any(role.id == 1342611104249024512 for role in ctx.author.roles):
            return await ctx.send("You don't have permission to use this command.", delete_after=10)
        try:
            duration = self.parse_time(time)
            self.log_action(member.id, "MUTE", reason, ctx.author.id)
            await member.timeout(duration, reason=reason)
            await self.dm_user(member, f"You have been muted for {time} for: {reason}")
            await ctx.send(f"{member.mention} has been muted for {time} for: {reason}")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    def parse_time(self, time_str: str) -> timedelta:
        """
        Parse a time string (e.g., 10s, 5m, 2h, 1d) into a timedelta.
        """
        match = re.match(r"(\d+)([smhd])", time_str)
        if not match:
            raise ValueError("Invalid time format. Use e.g. 10s, 5m, 2h, 1d.")
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == 's':
            return timedelta(seconds=amount)
        elif unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        else:
            raise ValueError("Invalid time unit.")

    @commands.command()
    async def softban(self, ctx, member: discord.Member, *, reason: str):
        """
        Softban a user: Ban and immediately unban to clear messages. Usage: !softban @user <reason>
        """
        if not any(role.id == 1342611104249024512 for role in ctx.author.roles):
            return await ctx.send("You don't have permission to use this command.", delete_after=10)
        try:
            self.log_action(member.id, "SOFTBAN", reason, ctx.author.id)
            await self.dm_user(member, f"You have been softbanned for: {reason}")
            await ctx.send(f"{member.mention} has been softbanned for: {reason}")
            await member.ban(delete_message_days=1, reason=reason)
            await ctx.guild.unban(member, reason="Softban: Unbanned after ban")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason: str):
        """
        Permanently ban a user. Usage: !ban @user <reason>
        """
        if not any(role.id == 1342611104249024512 for role in ctx.author.roles):
            return await ctx.send("You don't have permission to use this command.", delete_after=10)
        try:
            self.log_action(member.id, "BAN", reason, ctx.author.id)
            await self.dm_user(member, f"You have been banned for: {reason}")
            await ctx.send(f"{member.mention} has been banned for: {reason}")
            await member.ban(reason=reason)
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @commands.command()
    async def logs(self, ctx, member: discord.Member):
        """
        Display the moderation logs for a user in pages of 5 entries. Usage: !logs @user
        """
        if not any(role.id == 1342611104249024512 for role in ctx.author.roles):
            return await ctx.send("You don't have permission to use this command.", delete_after=10)
        try:
            self.cursor.execute(
                "SELECT log_id, action, reason, timestamp, moderator_id FROM logs WHERE user_id = ? ORDER BY timestamp DESC",
                (str(member.id),)
            )
            logs_data = self.cursor.fetchall()
            if not logs_data:
                return await ctx.send("No logs found for that user.")
            pages = [logs_data[i:i+5] for i in range(0, len(logs_data), 5)]
            current_page = 0
            embed = self.create_logs_embed(member, pages, current_page)
            view = LogsView(pages, current_page, member, self)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(f"Error: {e}")

    def create_logs_embed(self, member, pages, page_index):
        embed = discord.Embed(
            title=f"Logs for {member}",
            description="Below are the moderation logs:",
            color=discord.Color.blue()
        )
        for log in pages[page_index]:
            log_id, action, reason, timestamp, moderator_id = log
            embed.add_field(
                name=f"Log ID: {log_id} - {action}",
                value=f"Reason: {reason}\nModerator: <@{moderator_id}>\nTimestamp: {timestamp}",
                inline=False
            )
        embed.set_footer(text=f"Page {page_index+1} of {len(pages)}")
        return embed

    @commands.command()
    async def pardon(self, ctx, member: discord.Member):
        """
        Pardon a log entry (remove it from the database) for a user.
        Only allowed for moderators with roles 1342610409525608479 and 1342610501305372794.
        Usage: !pardon @user
        """
        allowed_roles = {1342610409525608479, 1342610501305372794}
        if not any(role.id in allowed_roles for role in ctx.author.roles):
            return await ctx.send("You don't have permission to pardon logs.", delete_after=10)
        try:
            self.cursor.execute(
                "SELECT log_id, action, reason, timestamp FROM logs WHERE user_id = ? ORDER BY timestamp DESC",
                (str(member.id),)
            )
            logs_data = self.cursor.fetchall()
            if not logs_data:
                return await ctx.send("No logs found for that user.")
            view = PardonView(member, logs_data, self)
            await ctx.send("Select a log to pardon:", view=view)
        except Exception as e:
            await ctx.send(f"Error: {e}")

# Pagination view for logs (5 logs per page)
class LogsView(discord.ui.View):
    def __init__(self, pages, current_page, member, cog):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = current_page
        self.member = member
        self.cog = cog

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.cog.create_logs_embed(self.member, self.pages, self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            embed = self.cog.create_logs_embed(self.member, self.pages, self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

# View for pardoning a log entry using a dropdown selection
class PardonView(discord.ui.View):
    def __init__(self, member, logs_data, cog):
        super().__init__(timeout=60)
        self.member = member
        self.logs_data = logs_data
        self.cog = cog
        options = []
        for log in logs_data:
            log_id, action, reason, timestamp = log
            label = f"{log_id} | {action}"
            description = f"{reason[:50]} at {timestamp}"
            options.append(discord.SelectOption(label=label, description=description, value=str(log_id)))
        self.add_item(LogSelect(options, member, cog))

class LogSelect(discord.ui.Select):
    def __init__(self, options, member, cog):
        super().__init__(placeholder="Select a log to pardon", min_values=1, max_values=1, options=options)
        self.member = member
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        log_id = self.values[0]
        self.cog.cursor.execute("DELETE FROM logs WHERE log_id = ?", (log_id,))
        self.cog.db.commit()
        await interaction.response.send_message(f"Log {log_id} pardoned for {self.member.mention}.", ephemeral=True)

# Asynchronous setup function for dynamic cog loading
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
