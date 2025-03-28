import discord
from discord.ext import commands
from discord.ui import View, Select

class DepartmentDropdown(Select):
    def __init__(self):
        # Define the dropdown options
        options = [
            discord.SelectOption(label="Dept 1", description="Get information about Dept 1."),
            discord.SelectOption(label="Dept 2", description="Get information about Dept 2."),
            discord.SelectOption(label="Dept 3", description="Get information about Dept 3."),
            discord.SelectOption(label="Dept 4", description="Get information about Dept 4."),
            discord.SelectOption(label="Dept 5", description="Get information about Dept 5."),
        ]

        super().__init__(
            placeholder="Choose a department...",  # Placeholder text
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Map the selected option to department-specific responses
        selected = self.values[0]
        message_map = {
            "Dept 1": "Dept 1 Info:\n**Discord Invite:** discordd invitationnnnn\n**Application Link:** specific dept info and (app link)",
            "Dept 2": "Dept 2 Info:\n**Discord Invite:** discordd invitationnnnn\n**Application Link:** specific dept info and (app link)",
            "Dept 3": "Dept 3 Info:\n**Discord Invite:** discordd invitationnnnn\n**Application Link:** specific dept info and (app link)",
            "Dept 4": "Dept 4 Info:\n**Discord Invite:** discordd invitationnnnn\n**Application Link:** specific dept info and (app link)",
            "Dept 5": "Dept 5 Info:\n**Discord Invite:** discordd invitationnnnn\n**Application Link:** specific dept info and (app link)",
        }

        # Send an ephemeral response with the mapped message
        await interaction.response.send_message(message_map[selected], ephemeral=True)

class DepartmentView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add the dropdown menu to the view
        self.add_item(DepartmentDropdown())

class Departments(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="embed_departments")
    async def embed_departments(self, ctx):
        """Sends the department embeds with dropdown options."""

        # First embed (with the image)
        first_embed = discord.Embed(color=discord.Color.blurple())
        first_embed.set_image(url="https://i.postimg.cc/7Z8SY0Z6/40face33-c6ad-4a5d-b402-5f7126e8325f.png")

        # Send the first embed
        await ctx.send(embed=first_embed)

        # Second embed (with department info)
        second_embed = discord.Embed(
            title="Department Information",
            description="(Insert department info generic)",
            color=discord.Color.blurple()  # Use blurple for consistency
        )

        # Add the dropdown menu as a view
        view = DepartmentView()
        await ctx.send(embed=second_embed, view=view)

# Setup function for adding the cog
async def setup(client):
    await client.add_cog(Departments(client))
