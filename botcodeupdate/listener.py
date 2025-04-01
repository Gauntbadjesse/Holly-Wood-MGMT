import discord
from discord.ext import commands
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("listener.log"),
        logging.StreamHandler()
    ]
)

class Listener(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        When the bot starts, perform the following actions:
        1. Delete and resend embeds created by the bot (sessions and departments).
        """
        logging.info("Listener cog is loaded. Scanning for embeds...")
        await self.resend_embeds()

    async def resend_embeds(self):
        """
        Resend the session and departments embeds by scanning all text channels
        and deleting previous bot embeds.
        """
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                if not channel.permissions_for(guild.me).manage_messages:
                    logging.warning(f"Missing permissions to manage messages in {channel.name}. Skipping...")
                    continue

                try:
                    # Delete bot's embeds in the channel
                    async for message in channel.history(limit=100):
                        if message.author == self.client.user and message.embeds:
                            if "Session" in message.embeds[0].title or "Departments" in message.embeds[0].title:
                                logging.info(f"Deleting embed in channel: {channel.name}")
                                await message.delete()

                    # Resend specific embeds
                    if channel.name.lower() == "sessions":
                        await self.send_sessions_embed(channel)
                    elif channel.name.lower() == "departments":
                        await self.send_departments_embed(channel)

                except Exception as e:
                    logging.error(f"Error processing channel {channel.name}: {e}")

    async def send_sessions_embed(self, channel):
        """
        Resend the sessions embed in the specified channel.
        """
        try:
            embed = discord.Embed(
                title="Sessions",
                description=(
                    "Sessions are held whenever 3 or more staff members are available to moderate for 30 minutes or more. "
                    "Once the staff vote has accord we will send a vote here for the community to vote whether or not we have a session. "
                    "In order to have a session we need at least 14 votes. If you would like to be notified when we host a session, "
                    "click the button below to get the **Sessions** role."
                ),
                color=0x00FF00
            )
            toggle_button = discord.ui.Button(label="Toggle Sessions Role", style=discord.ButtonStyle.primary)

            async def toggle_role_callback(interaction: discord.Interaction):
                user = interaction.user
                role = interaction.guild.get_role(1342612650571599922)  # Replace with Sessions role ID
                if not role:
                    await interaction.response.send_message("⚠️ The Sessions role was not found.", ephemeral=True)
                    return

                if role in user.roles:
                    await user.remove_roles(role)
                    await interaction.response.send_message(
                        "✅ You have been removed from the **Sessions** role.", ephemeral=True
                    )
                else:
                    await user.add_roles(role)
                    await interaction.response.send_message(
                        "✅ You have been added to the **Sessions** role.", ephemeral=True
                    )

            toggle_button.callback = toggle_role_callback
            view = discord.ui.View()
            view.add_item(toggle_button)

            await channel.send(embed=embed, view=view)
            logging.info(f"Resent sessions embed in {channel.name}")
        except Exception as e:
            logging.error(f"Error resending sessions embed in {channel.name}: {e}")

    async def send_departments_embed(self, channel):
        """
        Resend the departments embed in the specified channel.
        """
        try:
            embed = discord.Embed(
                title="Departments",
                description="Select a department from the dropdown below to learn more:",
                color=0x00FFFF
            )
            embed.add_field(name="LAPD", value="Los Angeles Police Department", inline=False)
            embed.add_field(name="LASD", value="Los Angeles Sheriff's Department", inline=False)
            embed.add_field(name="LAFD", value="Los Angeles Fire Department", inline=False)
            embed.add_field(name="LASP", value="Los Angeles State Patrol", inline=False)

            dropdown = discord.ui.Select(
                placeholder="Choose a department",
                options=[
                    discord.SelectOption(label="LAPD", description="Learn more about LAPD"),
                    discord.SelectOption(label="LASD", description="Learn more about LASD"),
                    discord.SelectOption(label="LAFD", description="Learn more about LAFD"),
                    discord.SelectOption(label="LASP", description="Learn more about LASP"),
                ]
            )

            async def dropdown_callback(interaction: discord.Interaction):
                if dropdown.values[0] == "LAPD":
                    await interaction.response.send_message("Learn more about LAPD!", ephemeral=True)
                elif dropdown.values[0] == "LASD":
                    await interaction.response.send_message("Learn more about LASD!", ephemeral=True)
                elif dropdown.values[0] == "LAFD":
                    await interaction.response.send_message("Learn more about LAFD!", ephemeral=True)
                elif dropdown.values[0] == "LASP":
                    await interaction.response.send_message("Learn more about LASP!", ephemeral=True)

            dropdown.callback = dropdown_callback
            view = discord.ui.View()
            view.add_item(dropdown)

            await channel.send(embed=embed, view=view)
            logging.info(f"Resent departments embed in {channel.name}")
        except Exception as e:
            logging.error(f"Error resending departments embed in {channel.name}: {e}")

# Setup function for dynamic cog loading
async def setup(client):
    await client.add_cog(Listener(client))
