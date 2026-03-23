from io import TextIOWrapper
import requests, time
from datetime import datetime, date
from threading import Thread


"""
        Author: kek/bitwise/kyza

        Date: 31/07/2023 (Monday) 3:59AM (BST)

"""

class DataCompareURI:

    def __init__(self: object,
                 url: str):
        
        self.session: requests.Session = requests.session()                   #   keep session
        self.url: str = url                                                   #   URL to compare data from
        self.difference: dict[list[str]] = {"added": [], "removed": []}                                       #   when change is detected, new data is stored in here
        self.change: bool = False
        self.change_data_time: str = ""
        self.new: list[str] = []
    
    #       setting baseline for data comparison
    #       called upon setup, and data change

    def set_baseline(
            self: object,
            data: str | list[str] = ""
        ) -> object:

        '''
        Creates baseline file in current directory for data comparison

        use argument "data" to not use a webAPI
        '''

        while (data == ""):
            response = self.session.get(self.url)
            match response.status_code:
                case 500, 404, 403, 402, 401, 404:
                    raise Exception("Error: Couldn't GET " + response.url)
                case 200:
                    data = response.text
                    break
        f: TextIOWrapper = open("baseline.txt", "w")
        f.write(data)                                                       #   if no data is directly input into data, use URL data
        f.close()
        return self
    
                                                                             #       called upon checking for changes

    def get_baseline(self) -> list:

        '''
        Reads baseline file in current directory for data comparison
        '''

        f: TextIOWrapper = open("baseline.txt", "r")
        d = f.read().split()
        f.close()
        return d
    
    #       main function, use await for faster load times

    async def baseline_has_changed(
            self: object,
            logname: str):

        '''
        Every 1 second the baseline file and web data are compared for a change

        After change is detected, the difference is accessible to the variable "difference"

        Then the difference is appended to a changes.txt file for logging of time + data changed
        '''

        self.difference: dict[list[str]] = {"added": [], "removed": []}     #       flushing "difference" data change incase of multiple runtime(s)
        self.change: bool = False                                           #       ^
        data: str = ""
        
        while True:
            baseline: list[str] = self.get_baseline()                       #       obtaining baseline once as to reduce load times of I/O operations
            self.new: list[str] = self.session.get(self.url).text.split()   #       the current data at our URL to compare with
            time.sleep(1)

            if self.new == baseline: continue 
            else:
                if "Error" in self.new:
                    print("Endpoint timeout - too many GET requests...")
                    time.sleep(5)
                    continue                                         
                self.change = True                                          
                self.change_date_time = f"{date.today()} - {datetime.now().hour}:{datetime.now().minute if datetime.now().minute >= 10 else f'0{datetime.now().minute}'}:{datetime.now().second if datetime.now().second >= 10 else f'0{datetime.now().second}'}"
                print(f"""There has been a data change
                    
                    time of change: {self.change_date_time}
                    """)
                for new_xuid in self.new:                                   #       every [line] in new data
                    if new_xuid not in baseline:                            #       [line] not inside baseline
                        self.difference["added"].append(new_xuid)           #       log new data change
                        
                if len(baseline) > len(self.new):                           #       entry removed from new baseline
                    for x in baseline:
                        if x not in self.new:
                            self.difference["removed"].append(x)
            break

        f = open("changes.txt", "a")                                        #       create/append new changes to output log file
        x = self.difference
        for a, b in x.items():
            for c in b:
                data += "\t\t\n" + c + f"{' removed' if not len(self.difference['added']) else ' added'}" + "\n"
        f.write(f"NEW {logname}(s):\n\nTime: {self.change_date_time}\n\nNew Entries: {data}\n\n")
        f.close()
        return self.set_baseline("\n\n".join(self.new))                     #       return class object + set change to new baseline for new runtime


