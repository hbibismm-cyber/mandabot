import discord
from discord import app_commands
from discord.ext import commands

from storage import get_honor_user, get_honor_leaderboard, add_honor, remove_honor


def get_tier(karma: int) -> str:
    if karma < 0:
        return "📰 Newspaper"
    elif karma < 5:
        return "🥉 Neutral"
    elif karma < 15:
        return "🥈 Trusted"
    else:
        return "🥇 Respected"


def build_leaderboard_embed(entries: list, page: int, per_page: int, names: dict) -> discord.Embed:
    total_pages = max(1, (len(entries) + per_page - 1) // per_page)
    start = page * per_page
    chunk = entries[start:start + per_page]

    embed = discord.Embed(title="⭐ KARMA LEADERBOARD ⭐", color=discord.Color.gold())
    lines = []
    for i, (user_id, karma) in enumerate(chunk, start=start + 1):
        name = names.get(user_id, f"Unknown ({user_id})")
        tier = get_tier(karma)
        lines.append(f"**{i}.** {name} — {tier} (**{karma}**)")

    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Page {page + 1} of {total_pages}")
    return embed


class LeaderboardView(discord.ui.View):
    def __init__(self, entries: list, names: dict, per_page: int = 10):
        super().__init__(timeout=60)
        self.entries = entries
        self.names = names
        self.per_page = per_page
        self.page = 0
        self.total_pages = max(1, (len(entries) + per_page - 1) // per_page)
        self.message = None
        self._update_buttons()

    def _update_buttons(self):
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    def current_embed(self) -> discord.Embed:
        return build_leaderboard_embed(self.entries, self.page, self.per_page, self.names)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)


class Honor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rep", description="Check a user's karma")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def rep(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        record = get_honor_user(target.id)

        if not record:
            await interaction.response.send_message(
                f"**{target.name}** has no karma yet."
            )
        else:
            tier = get_tier(record["karma"])
            await interaction.response.send_message(
                f"**{target.name}** — {tier}\n"
                f"Karma: **{record['karma']}**"
            )

    @app_commands.command(name="honorboard", description="View the karma leaderboard")
    async def honorboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        entries = get_honor_leaderboard(top_n=100)
        if not entries:
            await interaction.followup.send("No one has any karma yet.")
            return

        names = {}
        for user_id, _ in entries:
            try:
                user = await self.bot.fetch_user(int(user_id))
                names[user_id] = user.name
            except Exception:
                names[user_id] = f"Unknown ({user_id})"

        view = LeaderboardView(entries, names, per_page=10)
        view.message = await interaction.followup.send(embed=view.current_embed(), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Honor(bot))