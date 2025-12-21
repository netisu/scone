import httpx
import os
import json
from dotenv import load_dotenv
load_dotenv()

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def loadCogs():
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

@bot.event
async def on_ready():
    await loadCogs()
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="Netisu"))

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
