import requests as re
import json as j


class Info():
    info  = j.load(open("token.json", "r"))
    email = info['email']
    token = info['token']

class API():
    def __init__(self):
        self.baseApi = 'https://api.nature.global/1'
        self.header  = {'Authorization': 'Bearer '+ Info.token}

    def getMyInfo(self):
        api = self.baseApi + '/users/me'
        res = re.get(api, headers=self.header).json()
        # Formmating data for disabling "ensure_ascii" 
        # return j.dumps(res, indent=2, ensure_ascii=False) 
        return res

    def getDevices(self):
        api = self.baseApi + '/devices'
        res = re.get(api, headers=self.header).json()
        return res
    
    def getAppliances(self):
        api = self.baseApi + '/appliances'
        res = re.get(api, headers=self.header).json()
        return res

    # Editing
    # def getSignal(self, id):
    #     api = self.baseApi + f'/appliances/${id}/signals'
    #     res = re.get(api, headers=self.header).json()
    #     return res



if __name__ == "__main__":
    api = API()

    info = api.getMyInfo()
    print(info)