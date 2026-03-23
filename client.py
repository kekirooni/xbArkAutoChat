"""

            PyPy xbox library remastered

            Original Author:  Joe Alcorn

                    30/09/2014

            Author of Update and new features: kek/bitwise/kyza

                    31/07/2023

"""

from exceptions import InvalidReportType, InvalidRequest, InvalidReportReason, AuthFailed

import requests, re, json

from datetime import datetime

from tkinter import filedialog

from urllib.parse import urlencode, unquote, parse_qs, urlparse

MESSAGE_TEXT = 1
MESSAGE_GIF = 2
MESSAGE_GIF_TEXT = MESSAGE_TEXT | MESSAGE_GIF

GROUP_NOTI_NONE = 0
GROUP_NOTI_AT_ONLY = 1
GROUP_NOTI_ALL = 2

ARK_TITLE_ID: int = 983730484
CLUB_ID: int = 3379889510460425

class Client(object):
    
    def __init__(
        self: object
        ):
        self.session: requests.Session = requests.session()
        self.AUTHORIZATION_HEADER: str

    def todec_le(
            self: object,
            _hexstr: str
    ):
        ns = None
        if _hexstr[:1] == "0x":
            _hexstr = _hexstr.replace("0x", "")
        #   little endian
        count = len(_hexstr)
        ns = _hexstr[int(count/2):]     #   higher bit order
        ns += _hexstr[:int(count/2)]
        #   fixing unicode errors
        for idx, x in enumerate(ns):
            if  not x.isdigit():                                                #   catch } (7d)
                for z in bytes(x, "utf-8"):                                     #   } -> 0x7d
                    ns = ns.replace(x, hex(z).replace("0x", ""))        #   000001} -> 0000017d
        return int(f"0x{ns}", 16)

    def todec_be(
            self: object, 
            _hexstr: str
    ) -> int:
        if _hexstr[:1] == "0x":
            _hexstr = _hexstr.replace("0x", "")
        bedian: str = ""
        # big edian
        for id, c in enumerate(_hexstr):
            if "0" in c:
                continue
            bedian = _hexstr[id:]                                               #   000003f3 -> 3f3
            break
        # correcting pythons auto byte->string
        for idx, x in enumerate(bedian):
            if  not x.isdigit():                                                #   catch } (7d)
                for z in bytes(x, "utf-8"):                                     #   } -> 0x7d
                    bedian = bedian.replace(x, hex(z).replace("0x", ""))        #   000001} -> 0000017d

        return int(f"0x{bedian}", 16)

    def _raise_for_status(
        self: object,
        response: requests.Request
        ):
        if response.status_code == 400 or response.status_code == 429 or response.status_code == 404:
            try:
                description = f"Error {response.status_code}: {response.json()['errorMessage']}"
            except requests.exceptions.JSONDecodeError:
                description = 'Invalid request'
            if response.status_code == 429:
                wait = int(response.headers['RetryAfter'])
                raise InvalidRequest(f"Too many requests, try again after {wait} seconds, or {wait / 60} minutes ({wait / 3600} hours)")
            raise InvalidRequest(f"{response.status_code} Invalid Request ({description})")
        
    def _delete_json(
            self: object,
            url: str,
            data: dict | list,
            **kw: object
    ):
        headers = kw.pop("headers", {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')
        kw["headers"] = headers
        resp = self.session.delete(url, data=json.dumps(data), headers=headers)
        self._raise_for_status(resp)
        return resp
    
    def _delete(
            self: object,
            url: str,
            **kw: object
    ):
        headers = kw.pop("headers", {})
        headers.setdefault("Authorization", self.AUTHORIZATION_HEADER)
        kw["headers"] = headers
        resp = self.session.delete(url, **kw)
        self._raise_for_status(resp)
        return resp

    def _put_json(
        self: object,
        url: str,
        data: dict,
        **kw: object
    ):
        headers = kw.pop("headers", {})
        #headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')
        kw["headers"] = headers
        kw["data"] = json.dumps(data)
        resp = self.session.put(url, **kw)
        self._raise_for_status(resp)
        return resp
    
    def _put(
            self: object,
            url: str,
            **kw: object
    ):
        headers = kw.pop("headers", {})
        headers.setdefault("Authorization", self.AUTHORIZATION_HEADER)
        kw["headers"] = headers
        resp = self.session.put(url, **kw)
        self._raise_for_status(resp)
        return resp

    def _post(
        self: object,
        url: str,
        **kw: object
        ):
        '''
        Makes a POST request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = self.session.post(url, **kw)
        self._raise_for_status(resp)
        return resp
        
    def _post_json(
        self: object,
        url: str,
        data: dict,
        **kw: object
    ):
        '''
        Makes a POST request, setting Authorization
        and Content-Type headers by default
        '''
        data = json.dumps(data)
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')

        kw['headers'] = headers
        kw['data'] = data
        return self._post(url, **kw)
    
    def _get(
        self: object,
        url: str,
        **kw: object
        ):
        '''
        Makes a GET request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = self.session.get(url, **kw)
        return resp
    
    def change_gamertag(
            self: object,
            gamertag: str
    ):
        url = "https://gamertag.xboxlive.com/gamertags/reserve"
        resp = self.session.options(url, headers={
            "Accept": "*/*",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,x-xbl-contract-version",
            "Origin": "https://social.xbox.com",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Dest": "empty",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/100.0.0.0"
        })
        if(resp.status_code == 200):
            try:
                resp = self._post_json(url, data = {
                    "gamertag": gamertag,
                    "reservationId": self.user_xid,
                    "targetGamertagFields": "gamertag"
                }, headers = {
                    "x-xbl-contract-version": b"1"
                })
            except:
                print(f"Gamertag {gamertag} isnt allowed; try another")
                return
            info = resp.json()
            change = self._post_json("https://accounts.xboxlive.com/users/current/profile/gamertag",
                                     data = {
                                         "gamertag": {
                                                        "classicGamertag": info["classicGamertag"],
                                                        "gamertag": info["gamertag"],
                                                        "gamertagSuffix": info["gamertagSuffix"]
                                                     },
                                        "preview": "False",
                                        "reservationId": self.user_xid,
                                        "useLegacyEntitlement": "False"
                                     },
                                     headers= {
                                         "x-xbl-contract-version": b"6",
                                         "Accept": "application/json, text/plain, */*",
                                         "sec-ch-ua-platform": "Windows"
                                     })
            if change.status_code == 200:
                print(f"Gamertag changed to {info['gamertag']}")
                return 200
            else:
                print(f"Error: {change.status_code}")
                return change.status_code
    
    def change_gamerpic(
            self: object
    ):
        pass

    def auth(
        self: object,
        sLogin: str,
        sPassword: str
        ):
        login = sLogin
        base_url = 'https://login.live.com/oauth20_authorize.srf?'

            # if the query string is percent-encoded the server
            # complains that client_id is missing
        qs = unquote(urlencode({
                'client_id': '0000000048093EE3',
                'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
                'response_type': 'token',
                'display': 'touch',
                'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
                'locale': 'en',
            }))
        resp = self.session.get(base_url + qs)
        url_re = b'urlPost:\\\'([A-Za-z0-9:\?_\-\.&/=]+)'
        ppft_re = b'sFTTag:\\\'.*value="(.*)"/>'
        login_post_url = re.search(url_re, resp.content).group(1)
        post_data = {
                'login': sLogin,
                'passwd': sPassword,
                'PPFT': re.search(ppft_re, resp.content).groups(1)[0],
                'PPSX': 'Passpor',
                'SI': 'Sign in',
                'type': '11',
                'NewUser': '1',
                'LoginOptions': '1',
                'i3': '36728',
                'm1': '768',
                'm2': '1184',
                'm3': '0',
                'i12': '1',
                'i17': '0',
                'i18': '__Login_Host|1',
            }
        resp = self.session.post(
                login_post_url, data=post_data, allow_redirects=False,
            )
        if 'Location' not in resp.headers:
            # we can only assume the login failed
            msg = 'Could not log in with supplied credentials'
            raise AuthFailed(msg)

        # the access token is included in fragment of the location header
        location = resp.headers['Location']
        parsed = urlparse(location)
        fragment = parse_qs(parsed.fragment)
        access_token = fragment['access_token'][0]

        url = 'https://user.auth.xboxlive.com/user/authenticate'
        resp = self.session.post(url, data=json.dumps({
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token,
            }
        }), headers={'Content-Type': 'application/json'})

        json_data = resp.json()
        user_token = json_data['Token']
        uhs = json_data['DisplayClaims']['xui'][0]['uhs']

        url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
        resp = self.session.post(url, data=json.dumps({
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "UserTokens": [user_token],
                "SandboxId": "RETAIL",
            }
        }), headers={'Content-Type': 'application/json'})

        response = resp.json()
        self.AUTHORIZATION_HEADER = 'XBL3.0 x=%s;%s' % (uhs, response['Token'])
        self.user_xid = response['DisplayClaims']['xui'][0]['xid']
        self.user_gtg = response['DisplayClaims']['xui'][0]['gtg']
        self.authenticated = True
        print(f"{self.user_gtg} successfully logged in ({self.user_xid})\n")
        return self

    def fake_party_invite(
            self: object,
            victimXuid: int | str
    ):
        #   init party
        url = "https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/batch?reservations=false&followed=true&take=100"
        resp = self._post_json(url, data = {
            "xuids":
            [
                self.user_xid

            ]},
            headers={
                "x-xbl-contract-version": b"107",
                "User-Agent": "XBL-xComms-Win/1.0.0",
                "Content-Type": "application/json; charset=utf-8"
            })
        print(f"init party... {resp.status_code}")
        if resp.status_code == 200:
            #   create party
            resp = self._put_json("https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions/0C45BAB4-35D5-41A5-93C5-74375F2A2FFE",
                                  data = {
                                "constants": {
                                        "custom": {
                                            "bumblelion": "True",
                                            "xrnxbl": "True"
                                         }
                                 },
                                "members": {
                                    f"me_{self.user_xid}": {
                                        "constants": {
                                             "custom": {
                                                "clientCapability": 8
                                            },
                                            "system": {
                                                "xuid": self.user_xid
                                            }
                                        },
                                        "properties": {
                                            "custom": {
                                                "deviceId": "ca6789e6-61ce-41c2-85de-6a1fc699a118",
                                                "isBroadcasting": "False",
                                                "simpleConnectionState": 1,
                                                "voicesessionid": "!"
                                            }
                                        }
                                     }
                                },
                                "membersOnly": {
                                    "bumblelionRelayCreator": self.user_xid
                                },
                                "properties": {
                                    "system": {
                                        "joinRestriction": "followed",
                                        "readRestriction": "followed"
                                    }
                                }
                        }, headers={"x-xbl-contract-version": b"107", "Accept-Language": "en-GB", "Accept": "*/*"})
            print(f"create party... {resp.status_code}")
            print(str(resp.headers["X-Xbl-Debug"]).index("session="))
        if resp.status_code == 201 or resp.status_code == 200:
                #   invite victim to party
            resp = self._post_json("https://party.xboxlive.com/handles",
                                       data = {
                                           "invitedXuid": str(victimXuid),
                                           "sessionRef":{
                                               "name": "0C45BAB4-35D5-41A5-93C5-74375F2A2FFE",
                                               "scid": "7492BACA-C1B4-440D-A391-B7EF364A8D40",
                                               "templateName": "chat"
                                           },
                                           "type": "invite"
                                       },
                                       headers={"x-xbl-contract-version": b"107",
                                                "User-Agent": "XBL-xComms-Win/1.0.0"})
            print(f"invite to party... {resp.status_code}")
            if resp.status_code == 201:
                    #   delete party
                    """resp = self._put_json("https://party.xboxlive.com/serviceconfigs/7492BACA-C1B4-440D-A391-B7EF364A8D40/sessiontemplates/chat/sessions/0C45BAB4-35D5-41A5-93C5-74375F2A2FFE",
                                          data = {
                                              "members": {
                                                  f"me_{self.user_xid}": ""
                                                }
                                          }, headers={"x-xbl-contract-version": b"107", 
                                                      "User-Agent": "XBL-xComms-Win/1.0.0",
                                                      "If-Match": "*",
                                                      "Content-Type": "application/json; charset=utf-8"})"""

    def get_avatar_manifest(
        self: object,
        xuid: int | str,
        _new: bool = False
    ):
        print(xuid)
        url = f"https://avatarservices.xboxlive.com/users/xuid({xuid})/avatar/manifest" if not _new else f"https://avatarv3.xboxlive.com/users/xuid({xuid})/manifest"
        avatar_header = {"x-xbl-contract-version": b"2","content-type": "application/json; charset=UTF-8"} \
                        if not _new else {"x-xbl-contract-version": b"1", "Accept-Language": "en-GB",
                                               "Content-Type": "application/xml; charset=UTF-8", "x-xbl-build-version": "current",
                                               "x-xbl-api-build-version": "1.0", "Authorization": self.AUTHORIZATION_HEADER}
        try:
            return self._get(url, headers=avatar_header).content if _new else self._get(url, headers=avatar_header).json()["manifest"]["manifest"]
        except (ValueError, IndexError):
            Exception("Avatar manifest not found")
    
    def get_title_stats(
        self: object,
        xuid: int | str,
        titleId: int = ARK_TITLE_ID
    ):
        url = "https://userstats.xboxlive.com/batch"    #   URI WebApi
        resp = self._post_json(url, data =  {
                                        "arrangebyfield": "xuid",       #   get fields for XUID
                                        "groups": [{
                                            "name": "Hero",             #   Hero field, containing a group of StatList containers
                                            "titleId": titleId          #   the title index of the game
                                            }],
                                        "stats": [{
                                            "name": "MinutesPlayed",    #   ask to return minutes played
                                            "titleId": titleId          #   of the title
                                           }],
                                        "xuids": [xuid]                 #   list of xuids, > 1 will return a vector json
                                        }, headers={"x-xbl-contract-version": b"2", #   required
                                                    "accept-language": "en-GB"})    #   not sure if required, probably not
        #   post-get response formatted into JSON
        raw_json = resp.json()
        stats: dict = {}
        """
        example payload response:
                    'groups': [{
                                'name': 'Hero',
                                'titleid': '983730484',
                                'statlistscollection': [{
                                        'arrangebyfield': 'xuid',
                                        'arrangebyfieldid': '2533274905367855',
                                        'stats': [{
                                                'groupproperties': {
                                                    'Ordinal': '3',
                                                    'SortOrder': 'Descending',
                                                    'DisplayName': 'Creatures Tamed',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'CreatureTamed',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Creatures Tamed'
                                                }
                                            }, {
                                                'groupproperties': {
                                                    'Ordinal': '7',
                                                    'SortOrder': 'Descending',
                                                    'DisplayName': 'Survivors Killed',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'KilledSurvivor',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Survivors Killed'
                                                }
                                            }, {
                                                'groupproperties': {
                                                    'Ordinal': '10',
                                                    'SortOrder': 'Ascending',
                                                    'DisplayName': 'Player Deaths',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'PlayerDied',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Player Deaths'
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                        'statlistscollection': [{
                                'arrangebyfield': 'xuid',
                                'arrangebyfieldid': '2533274905367855',
                                'stats': [{
                                        'groupproperties': {},
                                        'xuid': '2533274905367855',
                                        'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                        'titleid': '983730484',
                                        'name': 'MinutesPlayed',
                                        'type': 'Integer',
                                        'value': '205763',
                                        'properties': {}
                                    }
                                ]
                            }
                        ]
                    }
        
        """
        #   going through each instance of a group StatList object
        for stat in raw_json["groups"][0]["statlistscollection"][0]["stats"]:
            try:
                #   storing the name:value into a directionary (key:value)
                stats[stat["name"]] = stat["value"]
            except (KeyError, IndexError):
                #   if stat doesnt have a value (0) skip adding the stat and avoid exception
                continue
        try:
            #   store the minuted played stat we requested in the POST JSON
            stats["MinutesPlayed"] = int(raw_json["statlistscollection"][0]["stats"][0]["value"])
        except (KeyError, IndexError):
            #   if value doesnt exist, aka 0, set a None object for error handling 
            stats["MinutesPlayed"] = None

        return stats

    def add_friend(
        self: object,
        xuid: int | str
    ):
        url = f"https://social.xboxlive.com/users/xuid({self.user_xid})/people/xuid({xuid})?app_name=xbox_on_windows&app_ctx=user_profile"
        return self._put(url, headers={"x-xbl-contract-version": b"2"}).status_code
    
    def delete_friend(
        self: object,
        xuid: int | str
    ):
        url = f"https://social.xboxlive.com/users/xuid({self.user_xid})/people/xuid({xuid})"
        return self._delete(url, headers={"x-xbl-contract-version": b"2"}).status_code
    
    def get_blocked_users(
        self: object
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        resp: json = self._get(url).json()
        data: list[str | int] = []
        try:
            data = resp["users"][0] #   there are blocked XUIDs
            data = resp["users"][:]
        except IndexError:
            data = ["No blocked users"]
        return data    
    
    def block_user(
        self: object,
        xuid: int | str
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        return self._put_json(url, data = {"xuid": xuid}, headers={"x-xbl-contract-version": b"4"}).status_code
    
    def unblock_user(
        self: object,
        xuid: int | str
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        return self._delete_json(url, data={"xuid": xuid}, headers={"x-xbl-contract-version": b"4"})

    def create_group(
            self: object,
            xuid: str | int | list[int] | list[str] = 0,
            groupName: str = ""
    ) -> int:
        url = "https://xblmessaging.xboxlive.com/network/xbox/users/me/groups"
        resp = self._post_json(url, data={"participants": ([2533274845171960] if not xuid else [xuid]) if "<class 'list'>" != str(type(xuid)) else xuid}, headers={"x-xbl-contract-version": b"1"})
        if groupName:
            self.change_group_name(int(resp.json()["groupId"]), groupName)
        return int(resp.json()["groupId"])

    def change_group_notification_status(
        self: object,
        groupID: int,
        statusID: int
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/notification"
        noti_options = [ "None",  "DirectMentions", "All" ]
        data = { "notificationOptions": noti_options[statusID] }
        return self._put_json(url, data=data, headers={"x-xbl-contract-version": b"1"})

    def change_group_name(
        self: object,
        groupID: int,
        new_name: str
    ) -> str:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/name"
        return self._post_json(url, data = {"name": new_name }).status_code

    def invite_to_group(
        self: object,
        groupID: int,
        xuid: str | int | list[int] | list[str]
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/participants"
        resp = self._post_json(url, data = {"participants": [xuid] if "<class 'list'>" != str(type(xuid)) else xuid})
        return resp.status_code
    
    def remove_from_group(
            self: object,
            groupID: int,       
            xuid: str | int     
    ) -> int:
        group_data = self._get("https://xblmessaging.xboxlive.com/network/xbox/users/me/groups",
                      headers={"x-xbl-contract-version": b"1"}).json()["groups"]
        for x in group_data:
            if str(groupID) in x.values():
                group_data = x
                break
        if str(xuid) in group_data["participants"]:
            url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/participants/xuid({xuid})"
            resp = self._delete(url, headers={"x-xbl-contract-version": b"1", "Accept": "application/json"})
            return resp.status_code
        else:
            raise Exception(f"User {xuid} is not in the specific group; no one to remove.")
    
    def message_to_group(
        self: object,
        groupID: int, 
        message: str
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/messages"
        resp = self._post_json(url, data={
                                     "parts": [{
                                             "contentType": "text",
                                             "version": 0,
                                             "text": message
                                          }]
                                     })
        return resp.status_code

    def image_to_group(
        self: object,
        groupID: int,
        _dir: str = "",
        message: str = "",
        isgif: bool = False
    ):
        #   get upload attachment ID and upload URI link
        url = { "upload_info":
                f"https://xblmessaging.xboxlive.com/network/xbox/users/me/upload/{'png' if not isgif else 'gif'}" }
        resp = self._get(url["upload_info"], headers={"x-xbl-contract-version": b"1"})

        url["uploadUri"] = resp.json()["uploadUri"]
        attachmentId = resp.json()["attachmentId"]

        # need to get image data

        name = filedialog.askopenfilename(title="Choose an Image to Send",filetypes=[("PNG","*.png"), ("JPEG", "*.jpeg"),("GIF" if isgif else "", "*.gif" if isgif else "")]) if _dir == "" else _dir
        with open(name, "rb") as f:
            imgdata = f.read()
        if(len(imgdata) > 7340032):
            raise Exception("ERROR: File size too big, must be < 7MB")
        if not isgif:
            width = self.todec_be(str(imgdata[0x10:0x14]).replace("b'", "").replace("'", "").replace("\\x", ""))
            height = self.todec_be(str(imgdata[0x14:0x18]).replace("b'", "").replace("'", "").replace("\\x", ""))
        else:
            width = self.todec_le(''.join(str(imgdata[0x6:0x8]).replace("b'", "").replace("'", "").split("\\x")))
            height = self.todec_le(''.join(str(imgdata[0x8:0xA]).replace("b'", "").replace("'", "").split("\\x")))

        # upload image to attachment servers, after 200 response, attachmentId represents our image
        # and response header contains the MD5 hash for our image
        
        md5 = self.session.put(url["uploadUri"],data=imgdata,
                                         headers = {
                                            "x-xbl-contract-version": b"3",
                                            "Content-Type": "application/octet-stream",
                                            "x-ms-blob-type": "BlockBlob"
                                             }).headers["Content-MD5"]

        # send the uploaded image attachment into the group chat
        
        url["messageUri"] = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/messages"
        resp = self._post_json(url["messageUri"],
                               data = {
                                    "parts": [{

                                             "attachmentId": attachmentId,
                                             "contentType": "image",
                                             "filetype": "png" if not isgif else "gif",
                                             "hash": md5,
                                             "height": height,
                                             "sizeInBytes": len(imgdata),
                                             "version": 0,
                                             "width": width
                                    
                                        }]
                                   },
                                   headers={
                                       "x-xbl-contract-version": b"1",
                                       "x-xbl-clientseqnum": b"1"
                                   })
        if message == "":
            return resp.status_code
        return [self.message_to_group(groupID, message), resp.status_code]
    
    def gamertag_from_xuid(
        self: object, xuid:int
        ) -> str:
        url = f"https://profile.xboxlive.com/users/xuid({xuid})/profile/settings"
        data = self.fetch(url)["settings"]
        for x in data:
            if x["id"] == "Gamertag":
                return x["value"]

    def gamer_profile(
            self: object,
            xuid: int | str = 0,
            gamertag: str = ""
    ) -> dict:
        edx: dict = {}
        url = f"https://profile.xboxlive.com/users/{f'gt({gamertag})' if not xuid else f'xuid({xuid})'}/profile/settings"
        profileMembers = [
            "AppDisplayName", "GameDisplayName", "Gamertag",
            "AppDisplayPicRaw", "GameDisplayPicRaw", "AccountTier",
            "TenureLevel", "Gamerscore", "DisplayPic",
            "PublicGamerpic", "XboxOneRep", "RealNameOverride",
            "ModernGamertagSuffix"
        ]
        resp = self._get(url + f"?settings={','.join(profileMembers)}",headers={"x-xbl-contract-version": b"3"})
        if resp.status_code == 404:
            print("No such user\n")
            return

        profileUsers = resp.json()["profileUsers"][0]
        edx["XUID"] = profileUsers["id"]
        for a in profileUsers["settings"]:
            edx[a["id"]] = a["value"]
        edx["isSponsoredUsers"] = profileUsers["isSponsoredUser"]
        return edx

    def get_profile_data(
            self: object,
            xuid: int | str = "",
            showFriends: bool = False
    ):
        url = f"https://peoplehub.xboxlive.com/users/xuid({xuid})/people/social/decoration/" if showFriends else \
              f"https://peoplehub.xboxlive.com/users/me/people/xuids({xuid})/decoration/"
        q = ["detail","preferredColor","presenceDetail","multiplayerSummary"]
        resp = self._get(url + ','.join(q), headers={"x-xbl-contract-version": b"5", "accept-language": "en-GB"})
        self._raise_for_status(resp)
        return resp.json()
    
    def xuid_from_gamertag(
        self: object, gt: str
        ) -> str:
        url = f'https://profile.xboxlive.com/users/gt({gt})/profile/settings'
        return self.fetch(url)["id"]

    def report_user(
        self: object,
        xuid: int | str,
        _type: str = "UserContentGamertag",
        reason: str = "cheating"
        ) -> requests.Request:
        url = f"https://reputation.xboxlive.com/users/xuid({xuid})/feedback"
        type_check = [
                        "UserContentGamertag",              #   Player name or Gamertag
                        "UserContentGamerpic",              #   Player Picture
                        "CommsVoiceMessage",                #   Voice Communication
                        "UserContentPersonalInfo"           #   Bio or Location
                     ]
        reason_check = [
                        "sexuallyInappropirate",            #   Sexually inappropriate
                        "violenceOrGore",                   #   Violence or gore
                        "harassment",                       #   Harassment
                        "spamOrAdvertising",                #   Spam or advertising
                        "terroristOrViolentExtremist",      #   Terrorist or violent extremist content
                        #   v   "under Something Else"    v
                        "imminentHarmPersonsOrProperty",    #   Imminent harm to persons or property
                         "hateSpeech",                      #   Hate speech
                         "fraud",                           #   Fraud
                         "cheating",                        #   Cheating
                         "csam",                            #   Child sexual exploitation or abuse
                         "drugsOrAlcohol",                  #   Drugs or alcohol
                         "profanity",                       #   Profanity
                         "selfHarmOrSuicide",               #   Self-harm or suicide
                         "other"                            #   Other
                        ]
        if reason not in reason_check:
            raise InvalidReportReason("incorrect report reason. please see: {reason_check}")
        if _type not in type_check:
            raise InvalidReportType("incorrect report type. please see: {type_check}")
        response = self._post_json(url, data = { "evidenceId": "(null)",
                                            "feedbackContext": "User",
                                            "feedbackType": _type,
                                            "textReason": f"{reason};" },
                              headers={"x-xbl-contract-version": "101"})
        return response

    def get_user_presence(
        self:object,
        xuid:int,
        level:str="all",
        is_group:bool = False
    ):
        presence_level = [ "user", "device", "title", "all" ]
        if level not in presence_level:
            Exception(f"Incorrect presence level. Try using: {presence_level}")
        url = f"https://userpresence.xboxlive.com/users/xuid({xuid})/groups/People?level={level}" \
              if is_group else f"https://userpresence.xboxlive.com/users/xuid({xuid})?level={level}"
        return self._get(url, headers={"x-xbl-contract-version": b"3","accept-language": "en-US"}).json()
    
    def message_user(
        self: object, xuid: str, _type: int, text:str, msg:str=""
        )-> int:
        """
                Author: kek/bitwise/kyza

                Makes a POST JSON request, with a message packet

                Conversation has to already exist for the other end to recieve (returns 200 SUCCESS regardless)

        """
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/conversations/users/xuid({xuid})"
        match _type:
            case 1:     #       TEXT
                response = self._post_json(url, data={
                                     "parts": [{
                                             "contentType": "text",
                                             "version": 0,
                                             "text": text
                                          }]
                                     })
            case 2:     #       GIF
                response = self._post_json(url, data={
                                    "parts": [{
                                            "contentType": "weblinkMedia",
                                            "mediaType": "gif",
                                            "mediaUri": text,
                                            "text": text,
                                            "version": 0
                                            }]
                                    }, headers={"x-xbl-contract-version": b"1"})
            case 3:     #       GIF + TEXT
                response = self._post_json(url, data={
                                    "parts": [{
                                            "contentType": "weblinkMedia",
                                            "mediaType": "gif",
                                            "mediaUri": text,
                                            "text": text,
                                            "version": 0
                                            },{
                                                 "contentType": "text",
                                                 "version": 0,
                                                 "text": msg
                                            }]
                                    }, headers={"x-xbl-contract-version": b"1"})
            case _:
                Exception("Incorrect message type; try: MESSAGE_TEXT, MESSAGE_GIF or MESSAGE_GIF_TEXT")
        return response.status_code
    
    def fetch(
            self: object, 
            url: str
    ):
        settings = [
                #'AppDisplayName',
                #'DisplayPic',
                #'Gamerscore',
                'Gamertag',
                #'PublicGamerpic',
                #'XboxOneRep',
                #"RealNameOverride",
                #"ModernGamertagSuffix"
            ]
        qs = '?settings=%s' % ','.join(settings)
        resp = self._get(url + qs, headers={'x-xbl-contract-version': b'3',})
        if resp.status_code == 404:
            print("No such user\n")      
        raw_json = resp.json()
        try:
            user = raw_json['profileUsers'][0]
        except KeyError:
            self._raise_for_status(resp)    #   rate limited
            print(raw_json)
        return user
