import os
from dotenv import load_dotenv
load_dotenv()

import random
import string

import discord
from discord import app_commands
from discord import ui
from discord.ext import commands

from utils.getNetizenValues import getSearchInformations
from utils.getNetizenValues import getImageHash

from database.database import add_user
from database.database import find_user

RoleID = int(os.getenv("verificationRoleID"))

def generateVerificationCode():
    epikCharacters = (
        string.ascii_letters +
        string.digits +
        "#@!"
    )
    return "verification|" + ''.join(random.choice(epikCharacters) for _ in range(12))

class VerificationView(ui.View):
    def __init__(self, userID, author_id: int, verification_code: str):
        super().__init__(timeout=10000) 
        self.author_id = author_id
        self.userID = userID
        self.verification_code = verification_code

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "You can't mess with a UI that isn't yours!",
                ephemeral=True
            )
            return False
        return True

    @ui.button(label="Verify", style=discord.ButtonStyle.success)
    async def confirm( self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        imageHash = await getImageHash(self.userID)
        searchInformations = await getSearchInformations(imageHash)
        if self.verification_code in searchInformations["description"]:
            role = interaction.guild.get_role(RoleID)
            user = interaction.user

            await user.add_roles(role)
            add_user(self.userID, interaction.user.id)

            await interaction.followup.send(
                "You have been officially verified!",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "You didn't put the verification code on your profile!",
                ephemeral=True
            )

        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "Verification canceled!",
            ephemeral=True
        )

        self.stop()


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="verification", description="⎡Main⎦ Verify who you are by ID.")
    @app_commands.describe(id="Account ID you want to be verified")

    async def verification(self, interaction:discord.Interaction, id: int):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.get_role(RoleID):
            await interaction.followup.send(
                "You are already linked with another ID!", ephemeral=True
            )
            return

        imageHash = await getImageHash(id)
        searchInformations = await getSearchInformations(imageHash)
        verificationCode = generateVerificationCode()

        embed = discord.Embed(title=f"Are you @{searchInformations["name"]}?",
                      url=f"https://netisu.com/@{searchInformations["name"]}",
                      description="> **If so, put Verification code at beginning of the description!**",
                      colour=0x6900d1)

        embed.set_author(name="Netisu Bot",
                        url="https://netisu.com/@Player",
                        icon_url="https://cdn.netisu.com/uploads/b2a715ae3b83a4b835d74b9c7575915f9b3c15c96de4.png")

        embed.add_field(name="**Verification Code**",
                        value=f"**`{verificationCode}`**",
                        inline=False)

        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{imageHash}_headshot.png")
        embed.set_footer(text="Netisu Bot")

        view = VerificationView(
            userID=id,
            author_id=interaction.user.id,
            verification_code=verificationCode
        )

        await interaction.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
        
async def setup(bot):
    await bot.add_cog(Verification(bot))