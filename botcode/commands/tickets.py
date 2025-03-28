import discord
from discord.ext import commands
from discord.ui import View, Button
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tickets.log"),
        logging.StreamHandler()
    ]
)

class TicketSystem(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.category_id = 1343649889220952064  # Ticket category
        self.log_channel_id = 1343648011854545009  # Logging channel
        self.support_channel_id = 1342668753183440927  # Channel to send embeds
        self.general_role_id = 1342611034116198420  # Role for general tickets
        self.report_roles = [1342610501305372794, 1342610409525608479]  # Roles for report/community tickets

    @commands.Cog.listener()
    async def on_ready(self):
        """Automatically initialize tickets when the bot restarts."""
        logging.info("Bot has restarted. Automatically triggering ticket system...")
        support_channel = self.client.get_channel(self.support_channel_id)
        if support_channel:
            # Simulate sending the !tickets command in the support channel
            await self.initialize_tickets(support_channel)

    @commands.command()
    async def tickets(self, ctx):
        """Command to manually initialize the ticket system."""
        if ctx.channel.id != self.support_channel_id:
            await ctx.send("This command can only be used in the designated support channel.", delete_after=10)
            return
        await self.initialize_tickets(ctx.channel)
        await ctx.message.delete()  # Automatically delete the user's !tickets command message

    async def initialize_tickets(self, channel):
        """Deletes previous bot messages and sends the ticketing embeds."""
        # Clear previous bot messages
        async for message in channel.history(limit=100):
            if message.author == self.client.user:
                await message.delete()

        # First Embed
        first_embed = discord.Embed(color=discord.Color.from_str("#2C2F33"))  # Darker grey
        first_embed.set_image(url="https://i.postimg.cc/4d5WpwnB/SUPPORT.webp")  # Updated image link
        await channel.send(embed=first_embed)

        # Second Embed with enhanced text
        second_embed = discord.Embed(
            title="📩 Need Assistance? Open a Ticket!",
            description=(
                "If you need help, we're here for you! Choose the appropriate category below to create a ticket:\n\n"
                "🛠 **General Support** – Have a question or need assistance? Open a ticket for general inquiries.\n\n"
                "⚠ **Report Issue** – Reporting a player or staff member? Provide details and any required proof.\n\n"
                "💰 **Community & Purchases** – For donations, purchases, or community-related topics, use this ticket.\n\n"
                "Click the button below that best fits your needs!"
            ),
            color=discord.Color.from_str("#23272A")  # Slightly darker grey
        )
        view = TicketButtons(self.client, self.category_id, self.general_role_id, self.report_roles, self.log_channel_id)
        await channel.send(embed=second_embed, view=view)

# Ticket Buttons
class TicketButtons(View):
    def __init__(self, client, category_id, general_role_id, report_roles, log_channel_id):
        super().__init__(timeout=None)
        self.client = client
        self.category_id = category_id
        self.general_role_id = general_role_id
        self.report_roles = report_roles
        self.log_channel_id = log_channel_id

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.green, emoji="🛠")
    async def general_button(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "gen", [interaction.user.id, self.general_role_id], "#1C6E19")  # Darker green

    @discord.ui.button(label="Report Issue", style=discord.ButtonStyle.red, emoji="⚠")
    async def report_button(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "rep", [interaction.user.id, *self.report_roles], "#7A0101")  # Darker red

    @discord.ui.button(label="Community & Purchases", style=discord.ButtonStyle.gray, emoji="💰")
    async def community_button(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "com", [interaction.user.id, *self.report_roles], "#846A29")  # Dark tan

    async def create_ticket(self, interaction, prefix, allowed_roles, embed_color):
        """Creates a ticket channel with appropriate permissions."""
        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=self.category_id)

        # Channel name with prefix and user name
        channel_name = f"{prefix}-{interaction.user.name[:4]}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
            return

        # Permissions setup
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Deny everyone by default
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),  # Allow the user
        }
        for role_id in allowed_roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Create the channel
        ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)

        # Notify in the ticket channel
        embed = discord.Embed(
            title="Ticket Opened!",
            description=f"{interaction.user.mention}, your ticket has been created! Support will assist you shortly.",
            color=discord.Color.from_str(embed_color)
        )
        await ticket_channel.send(content=f"{interaction.user.mention} @here", embed=embed)

        # Add a close button to the ticket
        await ticket_channel.send(view=CloseButton(ticket_channel, interaction.user.id, self.log_channel_id))

        # Log the ticket creation
        log_channel = guild.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(f"Ticket `{channel_name}` opened by {interaction.user.mention}.")

# Close Button
class CloseButton(View):
    def __init__(self, ticket_channel, user_id, log_channel_id):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel
        self.user_id = user_id
        self.log_channel_id = log_channel_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)
            return

        # Log ticket closure
        guild = interaction.guild
        log_channel = guild.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(f"Ticket `{self.ticket_channel.name}` closed by {interaction.user.mention}.")

        # Delete the ticket channel
        await self.ticket_channel.delete()

# Setup function for adding the cog
async def setup(client):
    await client.add_cog(TicketSystem(client))
