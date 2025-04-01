import logging
from discord.ext import commands
from discord import Embed, Interaction, ButtonStyle, ui
import asyncio

# Setup logging to display and record all levels
logging.basicConfig(
    level=logging.DEBUG,  # Log all levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sessions.log"),  # Output logs to sessions.log file
        logging.StreamHandler()  # Also print logs to the terminal
    ]
)

class Sessions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voters = set()  # To track voters
        self.vote_button = None  # Define the vote button dynamically

    @commands.command()
    async def ssv(self, ctx):
        """
        Starts a session vote, resets any previous data, and sends the startup embed when the vote threshold is met.
        Pings all voters who participated, logs events, and errors.
        """
        try:
            # Reset voters and button state every time the command is run
            self.voters = set()  # Clear all previous voter data
            self.vote_button = ui.Button(label="0/1", style=ButtonStyle.success)  # Reset button label
            logging.info(f"SSV command invoked by {ctx.author} (ID: {ctx.author.id}) and reset.")

            # Delete the !ssv command message
            await ctx.message.delete()

            # Role ping and session vote embed
            role = ctx.guild.get_role(1342612650571599922)  # Replace with actual Role ID
            embed = Embed(
                title="Session Vote",
                description="The staff Team has decided to host a session vote. Please vote below if you can attend today's session.",
                color=0xFFFF00
            )

            async def vote_callback(interaction: Interaction):
                try:
                    if interaction.user.id in self.voters:
                        await interaction.response.send_message("You have already voted!", ephemeral=True)
                        logging.debug(f"{interaction.user} attempted to vote again. Ignored.")
                        return

                    # Add the voter and update the button label
                    self.voters.add(interaction.user.id)
                    current_votes = len(self.voters)
                    self.vote_button.label = f"{current_votes}/1"
                    await interaction.message.edit(view=self.update_view())  # Update the view with the new label

                    # Log the vote
                    logging.info(f"{interaction.user} (ID: {interaction.user.id}) cast a vote ({current_votes}/1)")

                    if current_votes >= 1:  # Voting threshold reached (1 vote)
                        # Final session startup embed
                        ssu_embed = Embed(
                            title="SSU",
                            description=(
                                "Thank you to all who voted to host this session. Please be sure to join or you will face moderation actions.\n\n"
                                "**Below you can find our server information.**\n\n"
                                "Server owner: Faithful1909\n"
                                "Player Count: -/39\n"
                                "Queue: -\n"
                                "Staff members actively moderating."
                            ),
                            color=0x00FF00
                        )

                        # Ping voters
                        pings = []
                        for user_id in self.voters:
                            # Attempt to get member from cache
                            member = interaction.guild.get_member(user_id)
                            if not member:
                                # If not found, fetch the member directly
                                try:
                                    member = await interaction.guild.fetch_member(user_id)
                                except Exception as e:
                                    logging.error(f"Failed to fetch member with ID {user_id}: {e}")
                            if member:
                                pings.append(member.mention)
                            else:
                                logging.warning(f"Could not find or fetch member with ID {user_id}.")
                        pings_text = ", ".join(pings) if pings else "No voters to mention."
                        session_message = await ctx.send(pings_text, embed=ssu_embed)

                        # Log session startup
                        logging.info(f"Session startup initiated successfully with {len(self.voters)} voter(s).")

                        # Delete the original session vote embed
                        await interaction.message.delete()

                        # Delete pings after 5 minutes
                        await asyncio.sleep(300)
                        await session_message.edit(content=None)  # Remove pings
                        logging.debug("Voter pings removed after 5 minutes.")

                except Exception as e:
                    # Log any errors in the interaction
                    logging.error(f"Error in vote_callback: {e}")
                    await interaction.response.send_message("An error occurred during voting. Please try again later.", ephemeral=True)
                    await ctx.send(f"⚠️ An error occurred while processing your vote: `{e}`")

            # Assign the callback to the button
            self.vote_button.callback = vote_callback

            # Create and send view with the button
            view = self.update_view()
            await ctx.send(content=role.mention, embed=embed, view=view)
            logging.info("Session vote embed sent successfully.")

        except Exception as e:
            # Log any errors in the command
            logging.error(f"Error in ssv command: {e}")
            await ctx.send(f"⚠️ An error occurred while starting the session vote: `{e}`")

    def update_view(self):
        """
        Updates the view to reflect the current button state.
        """
        view = ui.View()
        view.add_item(self.vote_button)
        return view

    @commands.command()
    async def ssd(self, ctx, *, reason):
        """
        Sends the SSD embed with the provided reason.
        Logs all events and errors, and sends error messages to the chat.
        """
        try:
            # Log command execution
            logging.info(f"SSD command invoked by {ctx.author} (ID: {ctx.author.id}) with reason: {reason}")

            # Delete the !ssd command message
            await ctx.message.delete()

            # SSD embed with the provided reason
            embed = Embed(
                title="SSD",
                description=f"The Staff Team has decided to conclude today's session due to **{reason}**. Thank you so much for joining today and we will see you all next time!",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

            # Log successful SSD execution
            logging.info("SSD message sent successfully.")

        except Exception as e:
            # Log any errors in the command
            logging.error(f"Error in ssd command: {e}")
            await ctx.send(f"⚠️ An error occurred while concluding the session: `{e}`")

# Setup function for dynamic cog loading
async def setup(bot):
    await bot.add_cog(Sessions(bot))
