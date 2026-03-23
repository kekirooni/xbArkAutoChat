from datacompare import DataCompareURI
from client import Client
from exceptions import AuthFailed

import os, time, asyncio

from threading import Thread

CHEATER_GROUP = 29666265787923385

async def main():
    while True:
        print("Waiting for new bans...\n\n")
        await banList.baseline_has_changed("BAN")
        gName = xbox._get("https://xblmessaging.xboxlive.com/network/xbox/users/me/groups",
                      headers={"x-xbl-contract-version": b"1"}).json()["groups"][0]["groupName"]
        if "CHEATERS GET BANNED" not in gName:
            xbox.change_group_name(CHEATER_GROUP, "CHEATERS GET BANNED")
        for type, value in banList.difference.items():
            if not len(value): continue
            for xuid in value:
                if type == "removed":
                    print(f"{xbox.gamertag_from_xuid(xuid)} was either falsely banned & unbanned, or is a GM\n")
                    continue
                if xuid[:3] != "253":
                    _id = banList.difference["added"].index(xuid)
                    banList.difference["added"][_id] = xbox.xuid_from_gamertag(xbox.gamertag_from_xuid(xuid))
                    a = open("changes.txt", "r+")
                    d = a.read().replace(xuid, banList.difference["added"][_id])
                    a.write(d)
                    a.close()

            if len(banList.difference["added"]) < 17:
                xbox.invite_to_group(CHEATER_GROUP, banList.difference["added"]) 
            else:
                count = 0
                MAX_INVITES = 17
                while count < len(banList.difference["added"]):
                    count += MAX_INVITES - 1
                    if count <= MAX_INVITES:
                        xbox.invite_to_group(CHEATER_GROUP,banList.difference["added"][:count])
                    else:
                        xbox.invite_to_group(CHEATER_GROUP,banList.difference["added"][count:count+MAX_INVITES-1])   
            xbox.image_to_group(CHEATER_GROUP, os.getcwd() + "\\image\\banned.png", "Network Failure Message: You have been globally banned.")

if __name__ == "__main__":
    try:
        xbox: Client = Client()
        xbox.auth("redacted@outlook.com", "redacted")
        banList: DataCompareURI = DataCompareURI("http://arkdedicated.com/xboxbanlist.txt")
    except AuthFailed:
        raise "Incorrect email and/or password\n"
    try:
        f = open(os.getcwd() + "\\baseline.txt", "r")
        f.close()
    except FileNotFoundError:
        input("ERROR: setup.py has not been ran yet, please run setup.py first then xbox_ban_chat.py\n")
        exit()
    asyncio.run(main())
