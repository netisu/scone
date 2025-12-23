import httpx
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.getNetizenValue import getInventory
from utils.getNetizenValue import getUsername
from utils.getNetizenValue import getImageHash
from utils.getNetizenValue import getUserDescription
from utils.getNetizenValue import GetProfileValues

class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name="user", description="retrieves information from the selected player")
    @app_commands.describe(user="Player ID whose information you want to see")

    async def user(self, Interaction:discord.Interaction, user: int):
        await Interaction.response.defer()
        user = str(user)

        headshotImageHash = await getImageHash(user)
        username = await getUsername(headshotImageHash)
        embed = discord.Embed(title=f"@{username} Infomartion",
                      url=f"https://netisu.com/@{username}",
                      description=f"> **All the information shown was taken from various [APIs](https://netisu.com/@{username})**",
                      colour=0x6900d1)

        embed.set_author(name="Netisu Bot",
                        icon_url=f"https://cdn.netisu.com/thumbnails/{headshotImageHash}_headshot.png")
        
        description = await getUserDescription(headshotImageHash)
        embed.add_field(name="**Description**",
                        value=f"**`{description}`**",
                        inline=True)
        
        isOnline = str(httpx.get(f"https://netisu.com/api/users/online/{user}").json()["online"])
        embed.add_field(name="**Is Online**",
                        value=f"**`{isOnline}`**",
                        inline=True)
        
        inventory = await getInventory(user)
        embed.add_field(name="**Items Owned**",
                        value=f"**[`{len(inventory)}`](https://netisu.com/@{username}/inventory)**",
                        inline=True)
        
        userPricesValues = await GetProfileValues(user, inventory)
        embed.add_field(name="**Sparkles Spent**",
                        value=f"**`{userPricesValues[0]}`**",
                        inline=True)
        embed.add_field(name="**Sparkles RAP Value**",
                        value=f"**[`{userPricesValues[1]}`](https://netisu.com/market)**",
                        inline=True)

        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{headshotImageHash}.png")
        embed.set_footer(text="Netisu Bot")

        menu = discord.ui.Select(
            placeholder="Avatar Options",
            options=[
                discord.SelectOption(label="Placeholder!", value="normal"),
            ]
        )

        async def select_callback(altInteraction: discord.Interaction):
            if not altInteraction.user.id == Interaction.user.id:
                await altInteraction.response.send_message("You can't mess with a UI that isn't yours", ephemeral=True)
                return

        menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(menu)

        await Interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(User(bot))
    