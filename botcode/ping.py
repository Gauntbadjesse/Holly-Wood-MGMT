from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """
        Responds with the bot's latency in milliseconds.
        """
        latency = round(self.bot.latency * 1000)  # Convert latency to ms
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

# Proper async setup function for cog registration
async def setup(bot):
    await bot.add_cog(Ping(bot))  # Correctly await cog addition
