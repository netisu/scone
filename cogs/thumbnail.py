import discord
from discord import app_commands
from discord.ext import commands

from utils.getThumbnail import getThumbnail

allTypes = {
    "item": 1,
    "user": 2,
    "space": 3,
    "variation": 4
}
class Thumbnail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="thumbnail", description="⎡Utility⎦ Get the thumbnail you want by simply passing type and ID.")
    @app_commands.describe(type="Type of item you want to get thumbnail for(item, user, space, variation)", id="ID of item you want to pick")

    async def thumbnail(self, interaction:discord.Interaction, type: str, id: int):
        if not allTypes[type.lower()]:
            return
        
        numberType = allTypes[type.lower()]
        thumbnailResponse = await getThumbnail(numberType, id=id)
        embed = discord.Embed(title=f"Netisu {type.lower()} Thumbnail!",
                            description=f"> **This will retrieve thumbnail listed in the [API](https://netisu.com/api/thumbnails/{numberType}/{id})**",
                            colour=0x6900d1)

        embed.set_author(name="Netisu Bot",
                        icon_url="https://cdn.netisu.com/uploads/b2a715ae3b83a4b835d74b9c7575915f9b3c15c96de4.png")

        embed.set_image(url=thumbnailResponse)

        embed.set_footer(text="Netisu bot")

        await interaction.response.send_message(embed=embed)
        

async def setup(bot):
    await bot.add_cog(Thumbnail(bot))