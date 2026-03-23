from datacompare import DataCompareURI

if __name__ == "__main__":
    x = DataCompareURI("http://arkdedicated.com/xboxbanlist.txt")
    x.set_baseline()
    input("Setup done, now run xbox_ban_chat.py")