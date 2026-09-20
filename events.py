import random
import datetime
from random import randint

import discord
from discord.ext import commands, tasks
from storage import add_honor, remove_honor

from config import (
    ORDER_CHANNEL_ID, PURGE_CHANNEL_ID,
    NUKE_TARGET_ID, MANDRA_STICKER_ID,
    GOON_MESSAGES, VICTORIAN_URL, HATTO_URL,
    RANDOM_MSG_URL, BORN_TO_CAST_MSG,
)
from datetime import datetime, timezone



last_msg= datetime.now()
def get_seconds_difference(dt_val: datetime) -> float:
    if dt_val.tzinfo is not None and dt_val.tzinfo.utcoffset(dt_val) is not None:
        current_time = datetime.now(timezone.utc)
    else:
        current_time = datetime.now()
    duration = dt_val - current_time
    return duration.total_seconds()




def contains_goon(text: str) -> bool:
    import re

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = text.split()

    if "goon" in words:
        return True

    for i in range(len(words) - 1):
        if words[i] == "go" and words[i + 1] == "on":
            return True

    return False

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_random_send = None
        self.last_order_message_id = None
        self.weekly_purge.start()

    def cog_unload(self):
        self.weekly_purge.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        content = message.content.strip()
        user_message = content.lower()

        # +rep and -rep
        if content.startswith("+rep") or content.startswith("-rep"):
            if message.mentions:
                target = message.mentions[0]
                if content.startswith("+rep"):
                    success, msg = add_honor(target.id, message.author.id)
                    print("target",target.id,"+","targeter",message.author.id)
                else:
                    success, msg = remove_honor(target.id, message.author.id)
                    print("target",target.id,"-","targeter",message.author.id)
                await message.channel.send(msg)
            else:
                await message.channel.send("Mention a user to rep.")
            return

        # Reply to order replies
        if (
            message.channel.id == ORDER_CHANNEL_ID
            and message.reference is not None
            and message.reference.message_id == self.last_order_message_id
            and self.last_order_message_id is not None
        ):
            await message.reply("on it baws")

        # Sticker when mentioned
        if self.bot.user.mentioned_in(message):
            sticker = await self.bot.fetch_sticker(MANDRA_STICKER_ID)
            await message.channel.send(stickers=[sticker])

        # Random newspaper "go white boy go"
        if message.author.id == NUKE_TARGET_ID and random.randint(1, 100) == 1:
            await message.channel.send("go white boy go")
        # Goon word trigger
        if contains_goon(content):
            global last_msg
            if (get_seconds_difference(last_msg)<-60):
                await message.channel.send(random.choice(GOON_MESSAGES))
                last_msg=datetime.now()
            else:
                await message.channel.send(":mandragun:")


        # Victorian cuisine
        if user_message == "victorian cuisine":
            await message.channel.send(VICTORIAN_URL)

        # Weekly random message to torture newspaper
        if random.randint(1, 999) == 2:
            now = datetime.datetime.utcnow()
            if (
                self.last_random_send is None
                or now - self.last_random_send >= datetime.timedelta(days=7)
            ):
                await message.channel.send(BORN_TO_CAST_MSG)
                self.last_random_send = now
        #random msg

        # Hatto
        if user_message == "hatto":
            await message.channel.send(HATTO_URL)

    @tasks.loop(hours=168)
    async def weekly_purge(self):
        order_channel = self.bot.get_channel(ORDER_CHANNEL_ID)
        if order_channel is not None and randint(1, 5) == 4:
            try:
                sent = await order_channel.send("any new orders baws ?")
                self.last_order_message_id = sent.id
            except Exception as e:
                print(f"Failed to send order message: {e}")

        channel = self.bot.get_channel(PURGE_CHANNEL_ID)
        if channel is None:
            print("failed at censoring the bl*es")
            return

        deleted = 0
        async for msg in channel.history(limit=None, oldest_first=True):
            try:
                await msg.delete()
                deleted += 1
            except discord.Forbidden:
                print("the bl*es won.")
                return
            except discord.HTTPException:
                pass

        print(f"blues: deleted {deleted} messages")

    @weekly_purge.before_loop
    async def before_weekly_purge(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))