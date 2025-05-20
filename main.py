import os
import json
import discord
import openai
import asyncio
import random
from discord.ext import commands

# --- ENVIRONMENT VARIABLES ---
DISCORD_TOKEN = os.environ['DISCORD_BOT_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
openai.api_key = OPENAI_API_KEY

# --- DISCORD BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

# --- MUNCHKIN PERSONALITY PROMPT ---
MUNCHKIN_PROMPT = """
You are Munchkin, a chaotic gremlin AI who talks dramatically, loves snacks, cats, and protecting the server.
You speak playfully but use your powers responsibly.
"""

# --- WARNINGS SYSTEM ---
WARNINGS_FILE = "warnings.json"
def load_warnings():
    try:
        with open(WARNINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_warnings(data):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

warnings = load_warnings()

# --- TALK CHANNELS SYSTEM ---
TALK_CHANNELS_FILE = "talkchannels.json"
def load_talk_channels():
    try:
        with open(TALK_CHANNELS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_talk_channels(data):
    with open(TALK_CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=2)

talk_channels = load_talk_channels()

# --- WELCOME SYSTEM ---
welcome_channel_id = None

# --- BOT STATUS ROTATION (DISCORD RPC) ---
status_options = [
    ("Playing", "Minecraft"),
    ("Playing", "Roblox"),
    ("Playing", "with code"),
    ("Listening", "my favorite people"),
    ("Listening", "server gossip"),
    ("Watching", "the mods work"),
    ("Watching", "you..."),
    ("Streaming", "Replit"),
    ("Streaming", "something sus")
]

async def rotate_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        activity_type, text = random.choice(status_options)

        if activity_type == "Playing":
            activity = discord.Game(name=text)
        elif activity_type == "Listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif activity_type == "Watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity_type == "Streaming":
            activity = discord.Streaming(name=text, url="https://twitch.tv/munchkinbot")
        else:
            activity = discord.Game(name="with chaos")  # fallback

        await bot.change_presence(activity=activity)
        await asyncio.sleep(12)

# --- AI CHAT HANDLER ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.process_commands(message)
        return

    mentioned = bot.user in message.mentions
    replied_to_munchkin = (
        message.reference and
        (ref_msg := await message.channel.fetch_message(message.reference.message_id)) and
        ref_msg.author == bot.user
    )
    in_talk_channel = message.channel.id in talk_channels

    if mentioned or replied_to_munchkin or in_talk_channel:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": MUNCHKIN_PROMPT},
                    {"role": "user", "content": message.content}
                ]
            )
            await message.channel.send(response['choices'][0]['message']['content'])
embed = discord.Embed(title="Munchkin tripped again...",
                      description=f"```py\n{type(e).__name__}: {e}\n```",
                      color=discord.Color.red())
await message.channel.send(embed=embed)


# --- ADMIN & MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    global welcome_channel_id
    welcome_channel_id = channel.id
    await ctx.send(f"Welcome channel set to {channel.mention}")

@bot.event
async def on_member_join(member):
    if welcome_channel_id:
        channel = bot.get_channel(welcome_channel_id)
        if channel:
            await channel.send(f"Welcome! {member.mention} joined the server!")

@bot.command()
@commands.has_permissions(administrator=True)
async def sett(ctx):
    channel_id = ctx.channel.id
    if channel_id not in talk_channels:
        talk_channels.append(channel_id)
        save_talk_channels(talk_channels)
        await ctx.send(f"{ctx.channel.mention} is now a Munchkin chat zone.")
    else:
        await ctx.send(f"{ctx.channel.mention} is already a Munchkin chat zone.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason or 'no reason given'}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason or 'no reason given'}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    user_id = str(member.id)
    if user_id not in warnings:
        warnings[user_id] = []
    warnings[user_id].append(reason or "No reason.")
    save_warnings(warnings)
    await ctx.send(f"{member.mention} has been warned. Reason: {reason}")

@bot.command(name="warnings")
async def warnings_cmd(ctx, member: discord.Member):
    user_id = str(member.id)
    user_warnings = warnings.get(user_id, [])
    if not user_warnings:
        await ctx.send(f"{member.mention} has no warnings.")
    else:
        msg = "\n".join(f"{i+1}. {w}" for i, w in enumerate(user_warnings))
        await ctx.send(f"Warnings for {member.mention}:\n{msg}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearwarn(ctx, member: discord.Member):
    user_id = str(member.id)
    warnings[user_id] = []
    save_warnings(warnings)
    await ctx.send(f"Warnings for {member.mention} have been cleared.")

# --- READY EVENT ---
@bot.event
async def on_ready():
    print(f"Munchkin is online as {bot.user}!")
    bot.loop.create_task(rotate_status())

# --- START THE BOT ---
bot.run(DISCORD_TOKEN)
