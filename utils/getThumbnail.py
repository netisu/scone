import httpx
import re

async def getThumbnail(type: int, id: int):
    if type >= 5:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://netisu.com/api/thumbnails/{type}/{id}"
        )

        match = re.search( r"https://cdn\.netisu\.com/thumbnails/[^\"']+", resp.text )
        return match.group(0) if match else None
