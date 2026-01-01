import httpx

async def GetSkinValue(Items):
    totalSparkles = 0
    async with httpx.AsyncClient() as client:
        for itemType, itemId in Items.items():
            lastPage = (await client.get( f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page=1" )).json()["meta"]["last_page"]

            for index in range(1, lastPage + 1):
                actualPage = (await client.get( f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page={index}" )).json()["data"]
                
                for itemData in actualPage:
                    ID = itemData.get("id", "0")
                    if ID == itemId:
                        totalSparkles += itemData.get("cost_sparkles", 0)
    return int(totalSparkles)


EveryItemTypes = ["exclusive_all", "hat", "addon", "tool", "face", "tshirt", "shirt", "pants"]

async def getInventory(userID):
    inventory = []
    async with httpx.AsyncClient() as client:
            for itemType in EveryItemTypes:
                lastPage = (await client.get(f"https://netisu.com/api/{userID}/{itemType}?page=1")).json()["meta"]["last_page"]

                for index in range(1, lastPage + 1):
                    actualPage = (await client.get( f"https://netisu.com/api/{userID}/{itemType}?page={index}" )).json()["data"]
                    
                    for itemData in actualPage:
                        ID = itemData.get("id", "0")
                        inventory.append(ID)

    return inventory

async def GetProfileValues(userID, orgInventory: dict):
    if not orgInventory:
        inventory = await getInventory(userID)
    else:
        inventory = orgInventory.copy()

    totalSparkles = 0
    totalSparklesRAP = 0
    async with httpx.AsyncClient() as client:
        lastPage = (await client.get(
            f"https://netisu.com/api/items/{EveryItemTypes[0]}?sort=updated_at_desc&page=1"
        )).json()["meta"]["last_page"]

        for index in range(1, lastPage + 1):
            actualPage = (await client.get(
                f"https://netisu.com/api/items/{EveryItemTypes[0]}?sort=updated_at_desc&page={index}"
            )).json()["data"]
                
            for itemData in actualPage:
                ActualItemID = itemData.get("id", 0)
                if inventory and ActualItemID in inventory:
                    inventory.remove(ActualItemID)
                    totalSparklesRAP += itemData.get("cost_sparkles", 0)
                    totalSparkles += itemData.get("cost_sparkles", 0)

    async with httpx.AsyncClient() as client:
        for itemType in EveryItemTypes:
            if len(inventory) == 0:
                break

            lastPage = (await client.get(
                f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page=1"
            )).json()["meta"]["last_page"]

            for index in range(1, lastPage + 1):
                actualPage = (await client.get(
                    f"https://netisu.com/api/items/{itemType}?sort=updated_at_desc&page={index}"
                )).json()["data"]
                
                for itemData in actualPage:
                    ActualItemID = itemData.get("id", 0)
                    if inventory and ActualItemID in inventory:
                        inventory.remove(ActualItemID)
                        totalSparkles += itemData.get("cost_sparkles", 0)

    return [totalSparkles, totalSparklesRAP]

async def getImageHash(userId):
    async with httpx.AsyncClient() as client:
        return (await client.get(f"https://netisu.com/api/users/avatar-json/{userId}")).json()["Hash"]


async def getSearchInformations(imageHash):
    async with httpx.AsyncClient() as client:
        return (await client.get(f"https://netisu.com/api/search?search={imageHash}&limit=false")).json()[0]

async def userIsOnline(userID):
    async with httpx.AsyncClient() as client:
        return (await client.get(f"https://netisu.com/api/users/online/{userID}")).json()["online"]
