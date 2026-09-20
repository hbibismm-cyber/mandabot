import discord
from discord import app_commands
from discord.ext import commands

from config import MAKURA_ID, SAY_CHANNEL_ID


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="Internal use only")
    @app_commands.describe(message="Message to send")
    async def say(self, interaction: discord.Interaction, message: str):
        if interaction.user.id != MAKURA_ID:
            await interaction.response.send_message(
                "Mandrabot resists your attempt at mind control.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        target_channel = self.bot.get_channel(SAY_CHANNEL_ID)
        if target_channel is None:
            await interaction.followup.send("Target channel not found.", ephemeral=True)
            return

        await target_channel.send(message, allowed_mentions=discord.AllowedMentions.none())
        await interaction.followup.send("Message sent.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
