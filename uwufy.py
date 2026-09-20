from random import choice
import re
import discord
from discord.ext import commands
from discord import app_commands

triggerwords = ["hell", "fuck", "bitch", "bastard", "nah"]
replacement_words = ["he'ww", "fwick", "bwitch", "bastawd", "nyahh"]
uwus = ["uwu", "owo", "~~", ":3"]

LOG_CHANNEL_ID = 1540709807370018887


def uwuify(text):
    text = re.sub(r'[rl]', 'w', text)
    text = re.sub(r'[RL]', 'W', text)
    text = re.sub(r'([.!?])', lambda m: m.group(1) + ' ' + choice(uwus), text)
    text = re.sub(r'n([aeiou])', r'ny\1', text)
    for trigger, replacement in zip(triggerwords, replacement_words):
        text = re.sub(r'\b' + re.escape(trigger) + r'\b', replacement, text, flags=re.IGNORECASE)
    return text


class Uwyfy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locked: set[int] = set()
        self._webhook_cache: dict[int, discord.Webhook] = {}

    async def get_webhook(self, channel: discord.TextChannel) -> discord.Webhook:
        if channel.id in self._webhook_cache:
            return self._webhook_cache[channel.id]
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, name="uwulock-hook")
        if webhook is None:
            webhook = await channel.create_webhook(name="uwulock-hook")
        self._webhook_cache[channel.id] = webhook
        return webhook

    async def log_action(self, action: str, mod: discord.Member, target: discord.Member):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel is None:
            try:
                log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
            except discord.NotFound:
                print(f"Log channel {LOG_CHANNEL_ID} not found")
                return
            except discord.Forbidden:
                print(f"No permission to access log channel {LOG_CHANNEL_ID}")
                return

        embed = discord.Embed(
            title=f"UwuLock — {action}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Mod", value=f"{mod.display_name} (`{mod.id}`)", inline=True)
        embed.add_field(name="Target", value=f"{target.display_name} (`{target.id}`)", inline=True)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return
        if message.author.id not in self.locked:
            return

        try:
            webhook = await self.get_webhook(message.channel)
            await message.delete()
            await webhook.send(
                content=uwuify(message.content),
                username=message.author.display_name,
                avatar_url=message.author.display_avatar.url,
            )
        except discord.Forbidden:
            pass

    @app_commands.command(name="uwulock", description="Abandon all hope ye who use this command")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def uwulock(self, interaction: discord.Interaction, member: discord.Member):
        self.locked.add(member.id)
        await interaction.response.send_message(f"Added **{member.display_name}** to uwulock.")
        await self.log_action("Locked", interaction.user, member)

    @app_commands.command(name="uwuunlock", description="release a user from uwulock")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def uwuunlock(self, interaction: discord.Interaction, member: discord.Member):
        self.locked.discard(member.id)
        await interaction.response.send_message(f"Released **{member.display_name}** from uwulock.")
        await self.log_action("Unlocked", interaction.user, member)

    @uwulock.error
    @uwuunlock.error
    async def uwulock_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Your mortal mind cannot fathom such a destructive spell", ephemeral=True)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(Uwyfy(bot))