import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("session_command.log"),  # Create a dedicated log file for session commands
        logging.StreamHandler()  # Log to console for debugging
    ]
)

class Session(commands.Cog):
    def __init__(self, client):
        self.client = client

    # /ssv command
    @commands.command()
    async def ssv(self, ctx):
        logging.info(f"'!ssv' command triggered by {ctx.author} in channel #{ctx.channel} (Guild: {ctx.guild})")

        try:
            role_id = 1352726486104145983  # Role to ping
            required_votes = 2  # Votes required to start

            # Ping the role and delete the message
            role_ping = await ctx.send(f"<@&{role_id}>")
            await role_ping.delete()

            # Create the session vote embed
            embed = discord.Embed(
                title="Session Vote",
                description="A session vote has started! Vote to start up some great roleplays!",
                color=discord.Color.greyple()
            )
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="Vote now to join the fun!")

            # Set up the vote button
            view = SessionVoteView(client=self.client, required_votes=required_votes, ctx=ctx)
            await ctx.send(embed=embed, view=view)

            logging.info("Session vote embed sent successfully.")
        except Exception as e:
            logging.error(f"Error in '!ssv' command: {e}")
            await ctx.send(f"An error occurred while processing the '!ssv' command: {e}")

    # /ssd command
    @commands.command()
    async def ssd(self, ctx):
        logging.info(f"'!ssd' command triggered by {ctx.author} in channel #{ctx.channel} (Guild: {ctx.guild})")

        try:
            # Create the session shutdown embed
            embed = discord.Embed(
                title="Session Shutdown",
                description="Thanks for joining! Make sure to join back tomorrow!",
                color=discord.Color.red()
            )
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="We'll see you again soon!")

            await ctx.send(embed=embed)

            logging.info("Session shutdown embed sent successfully.")
        except Exception as e:
            logging.error(f"Error in '!ssd' command: {e}")
            await ctx.send(f"An error occurred while processing the '!ssd' command: {e}")


class SessionVoteView(View):
    def __init__(self, client, required_votes: int, ctx):
        super().__init__()
        self.votes = 0
        self.required_votes = required_votes
        self.client = client
        self.ctx = ctx
        self.voters = set()

    @discord.ui.button(label="0/2", style=discord.ButtonStyle.gray)
    async def vote_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.voters:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return

        self.voters.add(interaction.user.id)
        self.votes += 1
        button.label = f"{self.votes}/{self.required_votes}"
        await interaction.response.edit_message(view=self)

        if self.votes >= self.required_votes:
            # Delete the voting embed
            await interaction.message.delete()

            # Notify voters and start the session
            voter_mentions = " ".join([f"<@{voter_id}>" for voter_id in self.voters])
            await self.ctx.send(f"A session has started! Join up! {voter_mentions}")

            # Send server startup embed
            embed = discord.Embed(
                title="Server Startup",
                description="**Server:** Hollywood Roleplay | WL only.\n**Join Code:** LAHWRP\n**Player Count:** 0/39",
                color=discord.Color.green()
            )
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="Get ready to play!")
            await self.ctx.send(embed=embed)


# Setup function for adding the cog
async def setup(client):
    await client.add_cog(Session(client))
    logging.info("Session Cog loaded successfully.")
