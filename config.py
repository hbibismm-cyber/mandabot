# ── IDs ──────────────────────────────────────────────────────────────────────
PURGE_CHANNEL_ID   = 1346807075153645681
ORDER_CHANNEL_ID   = 1430331529099215031
SAY_CHANNEL_ID     = 1205588718774263860
MAKURA_ID          = 400140550503923713
NUKE_TARGET_ID     = 644586863881093120


# ── Roles & channels ──────────────────────────────────────────────────────────
ALLOWED_ROLE_IDS = {
    1315105809658544209,
    1395006533347180624,
    1315090029982384169,
    1345758044499476501,
    1385296517975375993,
    1315091467127230534,
    1315102680775135324,
    1238573370220740729,
    1346800838491897891,
    1315094176072732723,
}

# Maps channel_id → role_id (for reaction roles etc.)
ROLE_CHANNEL_MAP = {
    1346808567130230804: 1315105809658544209,
    1395007020163268669: 1395006533347180624,
    1346809772070141952: 1315090029982384169,
    1346806389359775846: 1345758044499476501,
    1346807075153645681: 1385296517975375993,
    1346806767228555345: 1315091467127230534,
    1346806929065771072: 1315102680775135324,
    1368902634437738617: 1238573370220740729,
}

# Reverse map: role_id → channel_id  (used by /insult)
ROLE_TO_CHANNEL = {role: channel for channel, role in ROLE_CHANNEL_MAP.items()}

# ── Assets ────────────────────────────────────────────────────────────────────
BRICK_GIF      = "https://tenor.com/view/cat-throwing-brick-brick-cat-gif-9142560192559212520"
PARRY_GIF      = "https://tenor.com/view/ultrakill-funny-cat-cat-parry-explode-gif-12515622299668151985"
NUKE_GIF       = "https://tenor.com/mB9C7DzBBge.gif"
IMMUNITY_GIF   = "https://tenor.com/b1SeM.gif"
MANDRAPET_GIF  = "https://media.discordapp.net/attachments/1462490936490856582/1462491111921549573/MANDY_SMILE_TRANS.gif"
PILLAR_GIF     = "https://media.discordapp.net/attachments/586588921614303233/1446964632970596372/10N04_Mandragora.gif"
VICTORIAN_URL  = "https://images-ext-1.discordapp.net/external/cgUQPEYpzmj7jm5D1R1lwVw_OHlHeaVU4XdY1W8E8T8/https/i.imgur.com/exNU6Rf.mp4"
HATTO_URL      = "https://media.discordapp.net/attachments/1432125742396735532/1453363990511091762/hatto.jpg"
RANDOM_MSG_URL = (
    "https://media.discordapp.net/attachments/1346809772070141952/1354376217410670698/"
    "SPOILER_picmix.com_12527279.gif?ex=696defa5&is=696c9e25&hm="
    "3ab21403e0ea38f6f5bd1227a646a312b8da8968a7e929f3f0aa8dad20705668&=&width=620&height=620"
)
MANDRA_STICKER_ID = 1274672953803669585

# ── Text lists ────────────────────────────────────────────────────────────────
INSULTS = [
    "stinky",
    "cringe",
    "lame",
    "embarrassing",
    "unwashed",
    "terminally online",
]

GOON_MESSAGES = [
    "good idea baws",
    "aye boss",
    "sounds right, baws",
    "whatever you say, baws",
    "you got it, boss",
    "yeah yeah, makes sense baws",
    "what the fuck is wrong with you baws",
    "on it baws",
]

BORN_TO_CAST_MSG = (
    "BORN TO CAST VICTORIA IS A FUCK 鬼神 Kill Em All 1091 "
    "I am rock cat410,757,864,530 DEAD VICTORIANS"
)