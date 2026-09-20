from __future__ import annotations
 
import random
import re
import time
from dataclasses import dataclass, field
from typing import Dict, Optional
 
import discord
from discord import app_commands
from discord.ext import commands, tasks
 
# ---------------------------------------------------------------------------
# Config: booze choices
# ---------------------------------------------------------------------------
 
# A gif shown whenever someone opens the bar. Swap this for whatever you like,
# or make it a list and pick randomly.
BAR_GIF_URL = "https://tenor.com/view/kitten-drink-milk-bar-cat-gif-11501109593153103379"
 
@dataclass(frozen=True)
class Booze:
    key: str
    label: str
    emoji: str
    description: str
    intensity: float   # 0.0 (stone sober) - 1.0 (can barely type)
    duration: int       # seconds the effect lasts
 
 
BOOZE_MENU = [
    Booze("beer", "Beer", "🍺", "Basic Ass", intensity=0.20, duration=90),
    Booze("wine", "Wine", "🍷", "Divorced Mom", intensity=0.35, duration=150),
    Booze("cocktail", "Cocktail", "🍸", "mediocre", intensity=0.55, duration=210),
    Booze("shot", "Whiskey Shot", "🥃", "Hits Hard", intensity=0.75, duration=180),
    Booze("moonshine", "Moonshine", "💀", "OOuGhHH", intensity=0.95, duration=300),
]
 
WEBHOOK_NAME = "bartender-impersonator"
 
 
# ---------------------------------------------------------------------------
# The "drunk" text filter
# ---------------------------------------------------------------------------
 
HICCUPS = ["*hic*", "hic!", "*hiccup*"]
SLUR_SUFFIXES = ["...", "~", "!!", " lol", " haha"]
 
VOWEL_SWAPS = {
    "a": ["a", "aa", "ah"],
    "e": ["e", "ee", "eh"],
    "i": ["i", "ii"],
    "o": ["o", "oo", "oh"],
    "u": ["u", "uu"],
}
 
 
def _slur_word(word: str, intensity: float) -> str:
    """Randomly mangle a single word based on intensity (0-1)."""
    if not word:
        return word
 
    chars = list(word)
    out = []
    for ch in chars:
        lower = ch.lower()
        # Randomly stretch vowels
        if lower in VOWEL_SWAPS and random.random() < intensity * 0.6:
            replacement = random.choice(VOWEL_SWAPS[lower])
            out.append(replacement.upper() if ch.isupper() else replacement)
            continue
        # Randomly swap adjacent letters later (handled after join)
        out.append(ch)
 
    result = "".join(out)
 
    # Occasionally swap two adjacent letters (typo-like slurring)
    if len(result) > 3 and random.random() < intensity * 0.35:
        i = random.randint(0, len(result) - 2)
        lst = list(result)
        lst[i], lst[i + 1] = lst[i + 1], lst[i]
        result = "".join(lst)
 
    # Occasionally drop the last letter entirely
    if len(result) > 3 and random.random() < intensity * 0.2:
        result = result[:-1]
 
    return result
 
 
def drunkify(text: str, intensity: float) -> str:
    """
    Apply a 'drunk filter' to a message. intensity is 0.0-1.0, higher = messier.
    Preserves mentions, custom emoji, and URLs untouched so pings/links still work.
    """
    if not text:
        return text
 
    # Don't mangle mentions, channel refs, custom emoji, or URLs.
    protect_pattern = re.compile(r"(<@!?\d+>|<#\d+>|<@&\d+>|<a?:\w+:\d+>|https?://\S+)")
    tokens = protect_pattern.split(text)
 
    out_tokens = []
    for token in tokens:
        if protect_pattern.fullmatch(token or ""):
            out_tokens.append(token)
            continue
 
        words = token.split(" ")
        slurred_words = []
        for w in words:
            if w == "":
                slurred_words.append(w)
                continue
            slurred_words.append(_slur_word(w, intensity))
        out_tokens.append(" ".join(slurred_words))
 
    result = "".join(out_tokens)
 
    # Sprinkle in hiccups
    hiccup_chance = intensity * 0.5
    words_list = result.split(" ")
    final_words = []
    for w in words_list:
        final_words.append(w)
        if w and random.random() < hiccup_chance / max(len(words_list), 1) * 10:
            final_words.append(random.choice(HICCUPS))
    result = " ".join(final_words)
 
    # Random trailing flourish
    if random.random() < intensity * 0.5:
        result += random.choice(SLUR_SUFFIXES)
 
    # ALL CAPS burst at higher intensity, for extra chaos
    if intensity > 0.7 and random.random() < 0.15:
        result = result.upper()
 
    return result
 
 
# ---------------------------------------------------------------------------
# UI: the booze selection dropdown
# ---------------------------------------------------------------------------
 
class BoozeSelect(discord.ui.Select):
    def __init__(self, cog: "Bartender"):
        self.cog = cog
        options = [
            discord.SelectOption(
                label=b.label,
                value=b.key,
                description=b.description,
                emoji=b.emoji,
            )
            for b in BOOZE_MENU
        ]
        super().__init__(
            placeholder="Pick your poison...",
            min_values=1,
            max_values=1,
            options=options,
        )
 
    async def callback(self, interaction: discord.Interaction):
        booze = next(b for b in BOOZE_MENU if b.key == self.values[0])
        self.cog.set_drunk(interaction.user.id, booze)
 
        await interaction.response.send_message(
            f"{booze.emoji} You knock back a **{booze.label}**. "
            f"Enjoy the next **{booze.duration}s**, {interaction.user.mention}...",
            ephemeral=True,
        )
 
 
class BoozeView(discord.ui.View):
    def __init__(self, cog: "Bartender", timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.add_item(BoozeSelect(cog))
 
 
# ---------------------------------------------------------------------------
# The Cog
# ---------------------------------------------------------------------------
 
@dataclass
class DrunkState:
    intensity: float
    expires_at: float
 
 
class Bartender(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.drunk_users: Dict[int, DrunkState] = {}
        # cache of webhooks per channel so we don't recreate them every message
        self._webhook_cache: Dict[int, discord.Webhook] = {}
        self._cleanup_loop.start()
 
    def cog_unload(self):
        self._cleanup_loop.cancel()
 
    # -- helpers -----------------------------------------------------------
 
    def set_drunk(self, user_id: int, booze: Booze) -> None:
        self.drunk_users[user_id] = DrunkState(
            intensity=booze.intensity,
            expires_at=time.time() + booze.duration,
        )
 
    def get_active_intensity(self, user_id: int) -> Optional[float]:
        state = self.drunk_users.get(user_id)
        if state is None:
            return None
        if state.expires_at <= time.time():
            self.drunk_users.pop(user_id, None)
            return None
        return state.intensity
 
    async def _get_webhook(self, channel: discord.TextChannel) -> Optional[discord.Webhook]:
        cached = self._webhook_cache.get(channel.id)
        if cached is not None:
            return cached
 
        try:
            webhooks = await channel.webhooks()
        except discord.Forbidden:
            return None
 
        webhook = discord.utils.get(webhooks, name=WEBHOOK_NAME)
        if webhook is None:
            try:
                webhook = await channel.create_webhook(name=WEBHOOK_NAME)
            except discord.Forbidden:
                return None
 
        self._webhook_cache[channel.id] = webhook
        return webhook
 
    @tasks.loop(seconds=30)
    async def _cleanup_loop(self):
        """Periodically clear out expired drunk states."""
        now = time.time()
        expired = [uid for uid, s in self.drunk_users.items() if s.expires_at <= now]
        for uid in expired:
            self.drunk_users.pop(uid, None)
 
    @_cleanup_loop.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()
 
    # -- slash command -------------------------------------------------------
 
    @app_commands.command(name="bar", description="Step up to the bar and order a drink.")
    async def bar(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🍻 Welcome to the Bar",
            description="What'll it be tonight?",
            color=discord.Color.gold(),
        )
        embed.set_image(url=BAR_GIF_URL)
 
        await interaction.response.send_message(
            embed=embed,
            view=BoozeView(self),
        )
 
    # -- message listener: the drunk effect ---------------------------------
 
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return  # webhooks only work in guild text channels
 
        intensity = self.get_active_intensity(message.author.id)
        if intensity is None:
            return
 
        content = message.content
        if not content and not message.attachments:
            return  # nothing to reprint
 
        webhook = await self._get_webhook(message.channel)
 
        # Delete the original message first.
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
 
        slurred = drunkify(content, intensity) if content else ""
 
        if webhook is None:
            # No webhook permission available: fall back to a plain bot message
            # instead of impersonation.
            if slurred:
                await message.channel.send(f"**{message.author.display_name}:** {slurred}")
            return
 
        display_name = message.author.display_name
        avatar_url = message.author.display_avatar.url
 
        try:
            await webhook.send(
                content=slurred or "\u200b",
                username=display_name,
                avatar_url=avatar_url,
                files=[await a.to_file() for a in message.attachments] if message.attachments else None,
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            )
        except discord.HTTPException:
            pass
 
 
async def setup(bot: commands.Bot):
    await bot.add_cog(Bartender(bot))