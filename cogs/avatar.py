import httpx
import asyncio
import json

import discord
from discord import app_commands
from discord.ext import commands

from utils.getNetizenValue import GetValue

def GetOnlyShowpieces(playerId: float, items):
    inventoryResponse = httpx.get("https://netisu.com/api/6/exclusive_all?page=1").json()
    lastPage = inventoryResponse["meta"]["last_page"]

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

class FilterModal(discord.ui.Modal, title="Item Filters"):
    def __init__(self, future: asyncio.Future):
        super().__init__()
        self.future = future 
        
    filters = discord.ui.TextInput(
        label="Enter filter types",
        placeholder="hat, addon, tool, face, tshirt, shirt, pants...",
        required=True,
        max_length=50
    )

    showpieceOnly = discord.ui.Label(
        text="Showpieces only?",
        description="Do you only want it to show showpieces?",
        component=discord.ui.Select(
            placeholder="Boolean",
            options=[
                discord.SelectOption(label='True', description="This will tell us that you only want to see showpieces", value="true"),
                discord.SelectOption(label='False', description="This will tell us that you dont want to see showpieces", value="false")
            ],
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.filters.value.lower()
        filtersArray = [f.strip() for f in raw.split(",") if f.strip()]

        validFilters = {"hat", "addon", "tool", "face", "tshirt", "shirt", "pants"}
        filtersArray = [f for f in filtersArray if f in validFilters]
        filtersArray.append(self.showpieceOnly.component.values[0])

        if not filtersArray:
            self.future.set_result([])
            return
        
        await interaction.response.defer(ephemeral=True)
        self.future.set_result(filtersArray)

class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="wearing", description="grab the skin of a selected player")
    @app_commands.describe(user="Player ID whose skin/avatar you want to see")
    
    async def wearing(self, OriginalInteraction:discord.Interaction, user: float):
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

        equippedItems = {}
        def createItemsField(itemsFilter):
            if not itemsFilter:
                itemsFilter = []

            embed.clear_fields()
            for item in currentlyResponse:
                name = item.get("name", "???")
                slug = item.get("slug", "N/S")
                item_id = item.get("id", "N/A")
                item_type = item.get("type", "")

                if itemsFilter and item_type not in itemsFilter:
                    continue

                emoji = emoji_types.get(item_type, "❄️")

                if item_id not in equippedItems:
                    equippedItems[item_type] = item_id
                
                if (itemsFilter and itemsFilter[-1] == "true") and slug in showpiecesItems:
                    embed.add_field(
                        name=f"**{emoji} {name}**",
                        value=f"[**`Market Link`**](https://netisu.com/market/item/{item_id}/{slug})",
                        inline=True
                    )
                elif (not itemsFilter or itemsFilter[-1] == "false"):
                    embed.add_field(
                        name=f"**{emoji} {name}**",
                        value=f"[**`Market Link`**](https://netisu.com/market/item/{item_id}/{slug})",
                        inline=True
                    )


            if len(itemsFilter) == 0:
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

        createItemsField(None)

        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{avatarHashImage}.png")
        embed.set_footer(text="Netisu Bot")

        menu = discord.ui.Select(
            placeholder="Avatar Options",
            options=[
                discord.SelectOption(label="Show Normal Avatar", value="normal"),
                discord.SelectOption(label="Select a filter", value="filter"),
                discord.SelectOption(label="Estimate price of Avatar", value="charvalue"),
                discord.SelectOption(label="Create Fetch", value="createfetch")
            ]
        )

        filters = discord.ui.TextInput(
            label="items that will only appear",
            placeholder="hat, addon, tool, face",
            required=True,
            max_length=40
        )

        avatarData = {
            "sparkles": -1,
            "stars": -1
        }
        
        async def select_callback(interaction: discord.Interaction):
            if not interaction.user.id == OriginalInteraction.user.id:
                await interaction.response.send_message("You can't mess with a UI that isn't yours :(", ephemeral=True)
                return

            choice = menu.values[0]
            if choice == "filter":

                future = asyncio.get_event_loop().create_future()
                modal = FilterModal(future)
                await interaction.response.send_modal(modal)

                filtersItems = await future
                createItemsField(filtersItems)
                await interaction.followup.edit_message(embed=embed, message_id=interaction.message.id)
            elif choice == "createfetch":
                item_ids = [item["id"] for item in currentlyResponse]
                colors = AvatarJsonResponse.get("RenderJson", {}).get("colors", {})
                await interaction.response.send_message(f"```javascript\n{generateFetchCode(item_ids, colors)}\n```", ephemeral=True)

            elif choice == "charvalue":
                await interaction.response.defer()

                if avatarData["sparkles"] < 0:
                    await interaction.followup.send( "This will take a while, please wait!", ephemeral=True )

                    avatarData["sparkles"] = await GetValue(equippedItems)
                    avatarData["stars"] = int(avatarData["sparkles"] / 10)

                embed.clear_fields()

                embed.add_field(
                    name="**✨ Sparkles**",
                    value=(
                        f"**`{avatarData["sparkles"]}`**"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="**🌟 Stars**",
                    value=(
                        f"**`{avatarData["stars"]}`**"
                    ),
                    inline=True
                )

                await interaction.edit_original_response(
                    content=None,
                    embed=embed
                )
            else:
                createItemsField(False)
                await interaction.response.edit_message(embed=embed)

        menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(menu)

        await OriginalInteraction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Users(bot))