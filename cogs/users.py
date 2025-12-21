import httpx
import json

import discord
from discord import app_commands
from discord.ext import commands

class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command()
    async def Wearing(self, interaction:discord.Interaction, playerID: int):
        currentlyResponse = httpx.get( f"https://netisu.com/api/inventory/currently-wearing/{playerID}" ).json()
        AvatarJsonResponse = httpx.get( f"https://netisu.com/api/users/avatar-json/{playerID}" ).json()

        embed = discord.Embed(title=f"Currently Wearing",
                        url="https://netisu.com/@Player",
                        description="> **This will retrieve all items listed in the [API](https://netisu.com/api/inventory/currently-wearing/6)**",
                        colour=0x6900d1)
        
        avatarHashImage = AvatarJsonResponse.get("Hash")
        embed.set_author(name="Netisu Bot",
                    url="https://netisu.com/@Player",
                    icon_url=f"https://cdn.netisu.com/thumbnails/{avatarHashImage}_headshot.png")
        
        emoji_types = {
            "hat": "🎩",
            "addon": "📦",
            "tool": "⚙️",
            "face": "👾",
            "tshirt": "👕",
            "shirt": "🧥",
            "pants": "👖"
        }

        for item in currentlyResponse:
            name = item.get("name", "???")
            slug = item.get("slug", "N/S")
            id = item.get("id", "N/A")
            item_type = item.get("type", "")

            emoji = emoji_types.get(item_type, "❄️")

            embed.add_field(
                name=f"**{emoji} {name}**",
                value=(
                    #f"Type: **`{item_type.capitalize()}`**\n"
                    #f"Market Link: [**`Market Link`**](https://netisu.com/market/item/{id}/{slug})"
                    f"[**`Market Link`**](https://netisu.com/market/item/{id}/{slug})"
                ),
                inline=True
            )
            
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

        embed.set_thumbnail(url=f"https://cdn.netisu.com/thumbnails/{avatarHashImage}.png")
        embed.set_footer(text="Netisu Bot")
        menu = discord.ui.Select(
            placeholder="Filter Options",
            options=[
                discord.SelectOption(label="Only Showpieces", value="showpieces"),
                discord.SelectOption(label="Create Fetch", value="createfetch")
            ]
        )

        async def select_callback(interaction: discord.Interaction):
            if menu.values[0] != "createfetch":
                return

            item_ids = [item["id"] for item in currentlyResponse]
            colors = AvatarJsonResponse.get("RenderJson", {}).get("colors", {})

            js_code = f"""async function equipFullAvatar() {{
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
            await interaction.response.send_message(f"```javascript\n{js_code}\n```", ephemeral=True)

        menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(menu)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Users(bot))

async def getOnlyShowpieces():
    return