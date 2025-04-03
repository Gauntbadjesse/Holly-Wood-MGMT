from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction, SelectOption, ui
import logging

class EmbedCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def embed(self, ctx):
        """
        Sends an embed with buttons to choose which detailed embed to send.
        Includes a "Sessions" embed with a role toggle button.
        Handles errors gracefully and provides detailed feedback.
        """
        try:
            # Create the initial embed
            embed = Embed(
                title="Choose an Embed",
                description="Which embed would you like to send?",
                color=0x00FFFF
            )

            # Create a button for Departments
            button_departments = ui.Button(label="Departments", style=ButtonStyle.primary)

            # Create a button for Sessions
            button_sessions = ui.Button(label="Sessions", style=ButtonStyle.success)

            # Callback for the Departments button
            async def send_departments(interaction: Interaction):
                try:
                    # Delete the original message
                    await interaction.message.delete()

                    # Create the Departments embed with short descriptions (10 words max each)
                    departments_embed = Embed(
                        title="Departments",
                        description="Select a department from the dropdown below to learn more:",
                        color=0x00FFFF
                    )
                    departments_embed.add_field(
                        name="LAPD",
                        value="Top-tier roleplay; strict and fair policing. Discord link available.",
                        inline=False
                    )
                    departments_embed.add_field(
                        name="LASD",
                        value="Realistic LEO, thriving assets. Apply to be a deputy.",
                        inline=False
                    )
                    departments_embed.add_field(
                        name="LAFD",
                        value="Low quota, easy-going; no inactivity strikes. Join today!",
                        inline=False
                    )
                    departments_embed.add_field(
                        name="CHP",
                        value="Elite highway patrol; only the best need apply.",
                        inline=False
                    )

                    # Create a dropdown menu for departments
                    options = [
                        SelectOption(label="LAPD", description="Learn more about LAPD"),
                        SelectOption(label="LASD", description="Learn more about LASD"),
                        SelectOption(label="LAFD", description="Learn more about LAFD"),
                        SelectOption(label="CHP", description="Learn more about CHP"),
                    ]
                    dropdown = ui.Select(placeholder="Choose a department", options=options)

                    # Define the callback for the dropdown interaction
                    async def dropdown_callback(interaction: Interaction):
                        try:
                            if dropdown.values[0] == "LAPD":
                                lapd_embed = Embed(
                                    title="Los Angeles Police Department (LAPD)",
                                    description=(
                                        "Here at LAPD we strive to give the best police roleplays while enforcing strict rules "
                                        "and preventing corrupt cops.\n\n"
                                        "You may apply by joining our relevant information below:\nDiscord server: (Link)"
                                    ),
                                    color=0x0000FF
                                )
                                await interaction.response.send_message(embed=lapd_embed, ephemeral=True)
                            elif dropdown.values[0] == "LASD":
                                lasd_embed = Embed(
                                    title="Los Angeles Sheriff's Department (LASD)",
                                    description=(
                                        "Are you interested in joining a thriving LEO department with realistic jurisdiction and superb assets? "
                                        "Then apply to be a WL Deputy with this link!\nDiscord server: (Discord link)"
                                    ),
                                    color=0x00FF00
                                )
                                await interaction.response.send_message(embed=lasd_embed, ephemeral=True)
                            elif dropdown.values[0] == "LAFD":
                                lafd_embed = Embed(
                                    title="Los Angeles Fire Department (LAFD)",
                                    description=(
                                        "Thinking, 'I want to be a WL member without the heavy LEO duty?' Look no further!\n"
                                        "LAFD offers a quota of just 1 hour per week, no inactivity strikes, and exceptional flexibility.\nJoin today!"
                                    ),
                                    color=0xFF0000
                                )
                                await interaction.response.send_message(embed=lafd_embed, ephemeral=True)
                            elif dropdown.values[0] == "CHP":
                                chp_embed = Embed(
                                    title="California Highway Patrol (CHP)",
                                    description=(
                                        "California Highway Patrol is only meant for the best of the best, do you have what it takes?"
                                    ),
                                    color=0xFFFF00
                                )
                                await interaction.response.send_message(embed=chp_embed, ephemeral=True)
                        except Exception as e:
                            logging.error(f"Error in dropdown callback: {e}")
                            await interaction.response.send_message(
                                f"⚠️ An error occurred while processing your selection: `{e}`", ephemeral=True
                            )

                    # Assign the callback to the dropdown
                    dropdown.callback = dropdown_callback

                    # Create a view for the dropdown
                    dropdown_view = ui.View()
                    dropdown_view.add_item(dropdown)

                    # Send the Departments embed with dropdown
                    await interaction.channel.send(embed=departments_embed, view=dropdown_view)

                except Exception as e:
                    logging.error(f"Error in Departments button callback: {e}")
                    await interaction.response.send_message(
                        f"⚠️ An error occurred while processing your request for the Departments embed: `{e}`",
                        ephemeral=True
                    )

            # Callback for the Sessions button
            async def send_sessions(interaction: Interaction):
                try:
                    # Delete the original message
                    await interaction.message.delete()

                    # Role ID for Sessions role
                    role_id = 1342612650571599922

                    # Create the Sessions embed
                    sessions_embed = Embed(
                        title="Sessions",
                        description=(
                            "Sessions are held whenever 3 or more staff members are available to moderate for 30 minutes or more. "
                            "Once the staff vote has accorded, we will send a community vote to decide on a session. "
                            "At least 14 votes are required. Click the button below to get the **Sessions** role and be notified."
                        ),
                        color=0x00FF00
                    )

                    # Create the button for toggling the Sessions role
                    toggle_button = ui.Button(label="Toggle Sessions Role", style=ButtonStyle.primary)

                    async def toggle_role_callback(interaction: Interaction):
                        """
                        Handles the button interaction to toggle the Sessions role for the user.
                        """
                        try:
                            user = interaction.user
                            role = interaction.guild.get_role(role_id)

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

                        except Exception as e:
                            logging.error(f"Error in toggle role callback: {e}")
                            await interaction.response.send_message(
                                f"⚠️ An error occurred while toggling your role: `{e}`", ephemeral=True
                            )

                    # Assign the toggle button callback
                    toggle_button.callback = toggle_role_callback

                    # Create a view and add the toggle button
                    toggle_view = ui.View()
                    toggle_view.add_item(toggle_button)

                    # Send the Sessions embed with the toggle button
                    await interaction.channel.send(embed=sessions_embed, view=toggle_view)

                except Exception as e:
                    logging.error(f"Error in Sessions button callback: {e}")
                    await interaction.response.send_message(
                        f"⚠️ An error occurred while processing your request for the Sessions embed: `{e}`", ephemeral=True
                    )

            # Assign callbacks to the buttons
            button_departments.callback = send_departments
            button_sessions.callback = send_sessions

            # Create a view for the buttons
            view = ui.View()
            view.add_item(button_departments)
            view.add_item(button_sessions)

            # Send the initial embed with the Departments and Sessions buttons
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            logging.error(f"Error in !embed command: {e}")
            await ctx.send(f"⚠️ An error occurred while processing your request: `{e}`")

# Async setup function for cog registration
async def setup(bot):
    await bot.add_cog(EmbedCommand(bot))
