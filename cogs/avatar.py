import httpx
import json

import discord
from discord import app_commands
from discord.ext import commands

def GetOnlyShowpieces(playerId: float, items):
    exclusiveResponse = httpx.get("https://netisu.com/api/6/exclusive_all?page=1").json()
    lastPage = exclusiveResponse["meta"]["last_page"]

    showpiecesItems = []
    for index in range(lastPage):
        exclusiveResponse = httpx.get(f"https://netisu.com/api/6/exclusive_all?page={index}").json()
        for exclusiveItem in exclusiveResponse["data"]:
            exclusiveSlug = exclusiveItem.get("slug", "...")
            for item in items:
                slug = item.get("slug", "???")
                if slug == exclusiveSlug:
                    showpiecesItems.append(exclusiveSlug)
        
    return showpiecesItems

def generateFetchCode(item_ids, colors):
    return f"""async function equipFullAvatar() {{
        const xsrfToken = decodeURIComponent(document.cookie.match(/XSRF-TOKEN=([^;]+)/)[1]);
        const headers = {{
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-XSRF-TOKEN': xsrfToken
        }};

        await fetch('https://netisu.com/api/avatar/update', {{
            method: 'POST',
            credentials: 'include',
            headers,
            body: JSON.stringify({{ action: 'reset' }})
        }}).then(r => r.json()).then(console.log);

        const items = {item_ids};
        for (const id of items) {{
            await fetch(`https://netisu.com/api/avatar/wear/${{id}}`, {{
            method: 'POST',
            credentials: 'include',
            headers,
            body: JSON.stringify({{ edit_style_id: null }})
            }}).then(r => r.json()).then(console.log);
        }}

        const colors = {json.dumps(colors)};
        for (const [part, color] of Object.entries(colors)) {{
            await fetch('https://netisu.com/api/avatar/update', {{
            method: 'POST',
            credentials: 'include',
            headers,
            body: JSON.stringify({{ action: 'color', body_part: part, color: `#${{color}}` }})
            }}).then(r => r.json()).then(console.log);
        }}

        console.log('Finished');
        }}
        equipFullAvatar();"""


class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="wearing", description="grab the skin of a selected player")
    @app_commands.describe(user="Player ID whose skin/avatar you want to see")
    
    async def wearing(self, interaction:discord.Interaction, user: float):
        user = str(user)
        currentlyResponse = httpx.get( f"https://netisu.com/api/inventory/currently-wearing/{user}" ).json()
        AvatarJsonResponse = httpx.get( f"https://netisu.com/api/users/avatar-json/{user}" ).json()

        embed = discord.Embed(
            title=f"Currently Wearing",
            url="https://netisu.com/@Player",
            description=f"> **This will retrieve all items listed in the [API](https://netisu.com/api/inventory/currently-wearing/{user})**",
            colour=0x6900d1
        )
        
        avatarHashImage = AvatarJsonResponse.get("Hash")
        embed.set_author(
            name="Netisu Bot",
            url="https://netisu.com/",
            icon_url=f"https://cdn.netisu.com/thumbnails/{avatarHashImage}_headshot.png"
        )
        
        showpiecesItems = GetOnlyShowpieces(user, currentlyResponse)
        emoji_types = {
            "hat": "🎩",
            "addon": "📦",
            "tool": "⚙️",
            "face": "👾",
            "tshirt": "👕",
            "shirt": "🧥",
            "pants": "👖",
            "showpiece": "👑"
        }
        
        def createItemsField(onlyShowpieces: bool):
            embed.clear_fields()
            for item in currentlyResponse:
                name = item.get("name", "???")
                slug = item.get("slug", "N/S")
                id = item.get("id", "N/A")
                item_type = item.get("type", "")

                emoji = emoji_types.get(item_type, "❄️")
                if onlyShowpieces and not showpiecesItems:
                    return True
                elif slug in showpiecesItems:
                    emoji = emoji_types["showpiece"]

                def createItemTypeField():
                    embed.add_field(
                        name=f"**{emoji} {name}**",
                        value=(
                            f"[**`Market Link`**](https://netisu.com/market/item/{id}/{slug})"
                        ),
                        inline=True
                    )

                if onlyShowpieces and slug in showpiecesItems:
                    createItemTypeField()
                else:
                    createItemTypeField()

            if not onlyShowpieces:
                colorsArray = AvatarJsonResponse["RenderJson"]["colors"]
                parts_order = [
                    ("Head", "Head"),
                    ("Torso", "Torso"),
                    ("RightArm", "Right Arm"),
                    ("RightLeg", "Right Leg"),
                    ("LeftArm", "Left Arm"),
                    ("LeftLeg", "Left Leg"),
                ]

                grouped = {}
                for key, display in parts_order:
                    color = colorsArray.get(key)
                    if not color:
                        continue
                    grouped.setdefault(color, []).append(display)

                lines = []
                if len(grouped) == 1:
                    only_color = next(iter(grouped))
                    lines.append(f"All: **`#{only_color}`**")
                else:
                    for color, parts in grouped.items():
                        part_label = "/".join(parts)
                        lines.append(f"{part_label}: **`#{color}`**")

                embed.add_field(
                    name="**🎨 Body Colors**",
                    value="\n".join(lines),
                    inline=False
                )

        createItemsField(False)

        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{avatarHashImage}.png")
        embed.set_footer(text="Netisu Bot")

        menu = discord.ui.Select(
            placeholder="Avatar Options",
            options=[
                discord.SelectOption(label="Show Normal Avatar", value="normal"),
                discord.SelectOption(label="Show Only Showpieces", value="showpieces"),
                discord.SelectOption(label="Character Value(w.i.p)", value="charValue"),
                discord.SelectOption(label="Create Fetch", value="createfetch")
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            choice = menu.values[0]
            if choice == "showpieces":
                if createItemsField(True):
                    await interaction.response.send_message("This player does not have any Showpiece equipped!", ephemeral=True)
                await interaction.response.edit_message(embed=embed)

            elif choice == "createfetch":
                item_ids = [item["id"] for item in currentlyResponse]
                colors = AvatarJsonResponse.get("RenderJson", {}).get("colors", {})
                await interaction.response.send_message(f"```javascript\n{generateFetchCode(item_ids, colors)}\n```", ephemeral=True)

            else:
                createItemsField(False)
                await interaction.response.edit_message(embed=embed)

        menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(menu)

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Users(bot))