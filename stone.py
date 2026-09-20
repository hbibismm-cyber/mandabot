import random
import discord
from discord import app_commands
from discord.ext import commands

from config import MAKURA_ID, NUKE_TARGET_ID, BRICK_GIF, PARRY_GIF, NUKE_GIF, IMMUNITY_GIF
from storage import load_stone_data, save_stone_data


class Stone(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stone_data = load_stone_data()

    @app_commands.command(name="stone", description="Attempt to stone another user")
    @app_commands.describe(user="User to stone")
    async def stone(self, interaction: discord.Interaction, user: discord.User):
        stoner_id = str(interaction.user.id)
        target_id = str(user.id)

        if user.id == MAKURA_ID:
            await interaction.response.send_message(
                f"makura has been granted stone immunity by the great mandra\n{IMMUNITY_GIF}",
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        if user.id == NUKE_TARGET_ID:
            self.stone_data[target_id] = self.stone_data.get(target_id, 0) + 1
            save_stone_data(self.stone_data)
            await interaction.response.send_message(
                f"{interaction.user.name} stones {user.name}\n{NUKE_GIF}",
                allowed_mentions=discord.AllowedMentions.none()
            )
            return

        if random.choice([True, False]):
            self.stone_data[target_id] = self.stone_data.get(target_id, 0) + 1
            save_stone_data(self.stone_data)
            await interaction.response.send_message(
                f"{interaction.user.name} stones {user.name}\n{BRICK_GIF}",
                allowed_mentions=discord.AllowedMentions.none()
            )
        else:
            self.stone_data[stoner_id] = self.stone_data.get(stoner_id, 0) + 1
            save_stone_data(self.stone_data)
            await interaction.response.send_message(
                f"{interaction.user.mention} you got parried!\n{PARRY_GIF}"
            )

    @app_commands.command(name="stoneboard", description="View the stoning leaderboard")
    async def stoneboard(self, interaction: discord.Interaction):
        if not self.stone_data:
            await interaction.response.send_message("No one has been stoned yet.", ephemeral=True)
            return

        sorted_board = sorted(self.stone_data.items(), key=lambda x: x[1], reverse=True)

        lines = []
        for i, (user_id, points) in enumerate(sorted_board[:10], start=1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                name = user.name
            except Exception:
                name = f"Unknown User ({user_id})"
            lines.append(f"**{i}.** {name} — **{points}**")

        await interaction.response.send_message("🪨 **STONING LEADERBOARD** 🪨\n" + "\n".join(lines))


async def setup(bot: commands.Bot):
    await bot.add_cog(Stone(bot))
