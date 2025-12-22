import httpx
ApiBase = "https://netisu.com/api/items/hat?sort=updated_at_desc&page=1"

async def GetValue(Items):
    totalSparkles = 0
    for itemType, itemId in Items.items():
        lastPage = httpx.get(
            f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page=1"
        ).json()["meta"]["last_page"]

        for index in range(1, lastPage + 1):
            actualPage = httpx.get(
                f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page={index}"
            ).json()["data"]
            
            for itemData in actualPage:
                ID = itemData.get("id", "0")
                if ID == itemId:
                    totalSparkles += itemData.get("cost_sparkles", 0)
    
    return int(totalSparkles)