import httpx
import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.getNetizenValues import getInventory
from utils.getNetizenValues import getSearchInformations
from utils.getNetizenValues import getImageHash
from utils.getNetizenValues import GetProfileValues
from utils.getNetizenValues import userIsOnline

from database.database import find_user
class User(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name="user", description="⎡Information⎦ Retrieves information from the selected player")
    @app_commands.describe(id="Player ID whose information you want to see")

    async def user(self, interaction:discord.Interaction, id: int):
        await interaction.response.defer()
        id = str(id)

        headshotImageHash = await getImageHash(id)
        searchInformations = await getSearchInformations(headshotImageHash)
        isOnline = await userIsOnline(id)

        userValues = { "inventory": {}, "priceValues": [] }

        embed = discord.Embed(title=f"@{searchInformations["name"]} Infomartion",
                      url=f"https://netisu.com/@{searchInformations["name"]}",
                      description=f"> **This will retrieve all information listed in the [API](https://netisu.com/@{searchInformations["name"]})**",
                         colour=0x6900d1)

        embed.set_author(name="Netisu Bot",
                        icon_url=f"https://cdn.netisu.com/uploads/b2a715ae3b83a4b835d74b9c7575915f9b3c15c96de4.png")
        

        embed.add_field(name="**Description**",
                        value=f"**`{searchInformations["description"]}`**",
                        inline=True)
        
        embed.add_field(name="**Is Online**",
                        value=f"**`{isOnline}`**",
                        inline=True)
        
        discordUser = find_user(id)
        if discordUser:
            embed.add_field(name="**Discord user**",
                            value=f"**<@!{discordUser["discordId"]}>**",
                            inline=True)
        
        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{headshotImageHash}.png")
        embed.set_footer(text="Netisu Bot")

        menu = discord.ui.Select(
            placeholder="Avatar Options",
            options=[
                discord.SelectOption(label="Show basic information", description="It estimates how much player spent!", value="getBasic"),
                discord.SelectOption(label="Show sparkles spent", description="It estimates how much player spent!", value="getValue"),
                discord.SelectOption(label="Get player inventory", description="Retrieve inventory pages!", value="GetInventory")
            ]
        )

        async def select_callback(altInteraction: discord.Interaction):
            if not altInteraction.user.id == interaction.user.id:
                await altInteraction.response.send_message("You can't mess with a UI that isn't yours", ephemeral=True)
                return
            
            choice = menu.values[0]
            if choice == "getValue":
                menu.options.pop(1)
                await altInteraction.response.defer()

                await altInteraction.edit_original_response(view=view)
                await altInteraction.followup.send("This takes time, so in the meantime you can run other commands!", ephemeral=True)

                if not userValues["inventory"]:
                    userValues["inventory"] = await getInventory(id)
                    userValues["priceValues"] = await GetProfileValues(id, userValues["inventory"])

                embed.add_field(name="**Items Owned**",
                                value=f"**[`{len(userValues["inventory"])}`](https://netisu.com/@{searchInformations["name"]}/inventory)**",
                                inline=True)
                
                userPricesValues = userValues["priceValues"]
                embed.add_field(name="**Sparkles Spent**",
                                value=f"**`{userPricesValues[0]}`**",
                                inline=True)
                
                embed.add_field(name="**Sparkles RAP Value**",
                                value=f"**[`{userPricesValues[1]}`](https://netisu.com/market)**",
                                inline=True)
                
                await altInteraction.edit_original_response(embed=embed, view=view)


        menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(menu)

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(User(bot))
    