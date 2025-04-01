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
            embed = Embed(title="Choose an Embed", description="Which embed would you like to send?", color=0x00FFFF)

            # Create a button for Departments
            button_departments = ui.Button(label="Departments", style=ButtonStyle.primary)

            # Create a button for Sessions
            button_sessions = ui.Button(label="Sessions", style=ButtonStyle.success)

            # Callback for the Departments button
            async def send_departments(interaction: Interaction):
                try:
                    # Delete the original message
                    await interaction.message.delete()

                    # Create the Departments embed
                    departments_embed = Embed(
                        title="Departments",
                        description="Select a department from the dropdown below to learn more:",
                        color=0x00FFFF
                    )
                    departments_embed.add_field(name="LAPD", value="Los Angeles Police Department", inline=False)
                    departments_embed.add_field(name="LASD", value="Los Angeles Sheriff's Department", inline=False)
                    departments_embed.add_field(name="LAFD", value="Los Angeles Fire Department", inline=False)
                    departments_embed.add_field(name="LASP", value="Los Angeles State Patrol", inline=False)

                    # Create a dropdown menu for departments
                    options = [
                        SelectOption(label="LAPD", description="Learn more about LAPD"),
                        SelectOption(label="LASD", description="Learn more about LASD"),
                        SelectOption(label="LAFD", description="Learn more about LAFD"),
                        SelectOption(label="LASP", description="Learn more about LASP"),
                    ]
                    dropdown = ui.Select(placeholder="Choose a department", options=options)

                    # Define the callback for dropdown interaction
                    async def dropdown_callback(interaction: Interaction):
                        try:
                            if dropdown.values[0] == "LAPD":
                                lapd_embed = Embed(title="Los Angeles Police Department (LAPD)", color=0x0000FF)
                                lapd_embed.add_field(name="Description", value="Learn more about LAPD here!")
                                await interaction.response.send_message(embed=lapd_embed, ephemeral=True)
                            elif dropdown.values[0] == "LASD":
                                lasd_embed = Embed(title="Los Angeles Sheriff's Department (LASD)", color=0x00FF00)
                                lasd_embed.add_field(name="Description", value="Learn more about LASD here!")
                                await interaction.response.send_message(embed=lasd_embed, ephemeral=True)
                            elif dropdown.values[0] == "LAFD":
                                lafd_embed = Embed(title="Los Angeles Fire Department (LAFD)", color=0xFF0000)
                                lafd_embed.add_field(name="Description", value="Learn more about LAFD here!")
                                await interaction.response.send_message(embed=lafd_embed, ephemeral=True)
                            elif dropdown.values[0] == "LASP":
                                lasp_embed = Embed(title="Los Angeles State Patrol (LASP)", color=0xFFFF00)
                                lasp_embed.add_field(name="Description", value="Learn more about LASP here!")
                                await interaction.response.send_message(embed=lasp_embed, ephemeral=True)
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
                        f"⚠️ An error occurred while processing your request for the Departments embed: `{e}`", ephemeral=True
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
                            "Once the staff vote has accord we will send a vote here for the community to vote whether or not we have a session. "
                            "In order to have a session we need at least 14 votes. If you would like to be notified when we host a session, "
                            "click the button below to get the **Sessions** role."
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
