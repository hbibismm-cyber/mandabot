import os
import io
import random
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw

from config import (
    INSULTS, MANDRAPET_GIF, PILLAR_GIF,
    ROLE_TO_CHANNEL,
)


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hug", description="Hug another user")
    @app_commands.describe(user="User to hug")
    async def hug(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()

        background_path = os.path.join(os.path.dirname(__file__), "Mandra_Hug2.jpeg")

        if not os.path.exists(background_path):
            await interaction.followup.send("Hug image missing on server.")
            return

        avatar_url = user.display_avatar.replace(size=256, format="png").url
        headers = {"User-Agent": "DiscordBot (Mandrabot)"}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(avatar_url) as av_resp:
                if av_resp.status != 200:
                    await interaction.followup.send("Failed to load avatar.")
                    return
                avatar_bytes = await av_resp.read()

        background = Image.open(background_path).convert("RGBA")
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

        avatar_size  = 210
        outline_size = 6
        avatar = avatar.resize((avatar_size, avatar_size))

        total_size = avatar_size + outline_size * 2
        outline = Image.new("RGBA", (total_size, total_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(outline)
        draw.ellipse((0, 0, total_size, total_size), fill=(0, 0, 0, 255))

        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar.putalpha(mask)

        outline.paste(avatar, (outline_size, outline_size), avatar)

        bg_w, bg_h = background.size
        position = (
            (bg_w - total_size) // 2 - 15,
            (bg_h - total_size) // 2 + 145,
        )
        background.paste(outline, position, outline)

        buffer = io.BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)

        await interaction.followup.send(file=discord.File(buffer, filename="hug.png"))

    @app_commands.command(name="mandrapet", description="mandra pet")
    async def mandrapet(self, interaction: discord.Interaction):
        await interaction.response.send_message(MANDRAPET_GIF)

    @app_commands.command(name="pillar", description="pillar")
    async def pillar(self, interaction: discord.Interaction):
        await interaction.response.send_message(PILLAR_GIF)

    @app_commands.command(name="feedmandra", description="Feed the Mandra bot some rock candy!")
    async def feedmandra(self, interaction: discord.Interaction):
        if random.randint(1, 10) == 1:
            await interaction.response.send_message("you fed it a rock. <:KILL:1471974665252507814>")
        else:
            await interaction.response.send_message("you fed mandrabot candy! <:mandralove:1474115259659714816>")

    @app_commands.command(name="insult", description="Insult another role in their channel")
    @app_commands.describe(role="Role to insult")
    async def insult(self, interaction: discord.Interaction, role: discord.Role):
        member = interaction.user

        caller_role = None
        for r in member.roles:
            if r.id in ROLE_TO_CHANNEL:
                caller_role = r
                break

        if caller_role is None:
            await interaction.response.send_message("You don't have permission to insult anyone.", ephemeral=True)
            return

        if role.id not in ROLE_TO_CHANNEL:
            await interaction.response.send_message("That role cannot be insulted.", ephemeral=True)
            return

        target_channel_id = ROLE_TO_CHANNEL[role.id]
        target_channel = interaction.guild.get_channel(target_channel_id)

        if target_channel is None:
            await interaction.response.send_message("Target channel not found.", ephemeral=True)
            return

        insult_word = random.choice(INSULTS)

        if role.id == caller_role.id:
            await target_channel.send(f"{interaction.user.name}, you called your own role **{insult_word}**. Embarrassing.")
        else:
            await target_channel.send(f"{role.name}, {caller_role.name} called you **{insult_word}**.")

        await interaction.response.send_message(f"Insult delivered to {target_channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
