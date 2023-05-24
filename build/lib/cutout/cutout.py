import json
import os
import re
from time import sleep

import requests

from .email_service import TempMail

CUTOUT_REG = "https://restapi.cutout.pro/user/registerByEmail2?email={email}&password={password}&vsource="
CUTOUT_ACTIVATION = "https://restapi.cutout.pro/user/activeEmail?token={token}"
# response {
#     "code": 0,
#     "data": {
#         "id": 409168116515077,
#         "mobile": null,
#         "email": "mllmzux4di@wuuvo.com",
#         "avatar": null,
#         "createdAt": 1682030961696,
#         "userType": null,
#         "userName": null,
#         "registerSite": null,
#         "api_show_report": 0,
#         "tags": null,
#         "init_password": false,
#         "wxOpenId": null,
#         "wxNickName": null,
#         "wxAvatar": null,
#         "isWhitelist": null,
#         "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJhdXRoMCIsImp0aSI6IjQwOTE2ODExNjUxNTA3NyJ9.IgaXID3njvPfFanCu9aCbpoWo_fSdCZd2lp0ynntjlb7kt5lJKwJMmbYxlkTBhWkQjv1l6zciYKfZs7LqsDfQQ"
#     },
#     "msg": "",
#     "time": 1682030961698
# }

CUTOUT_SECRET_KEY = "https://restapi.cutout.pro/user/apikey"
# {"code":0,"data":"283b50a369904e70a0f9c02696259169","msg":"","time":1682031199559}

CUTOUT_IMAGE_ENHANCE = "https://www.cutout.pro/api/v1/matting?mattingType=18&outputFormat={format}"
CUTOUT_BACKGROUND_REMOVE = "https://www.cutout.pro/api/v1/matting?mattingType=6"

class CutoutProClient:
    def __init__(self):
        self.email = None
        self.token = None
        self.secret_key = None
        try:
            if os.path.exists("key.json"):
                self.init_from_local()
                return
        except:
            pass

        self.init_from_new_email()


    def init_from_local(self):
        with open("key.json") as f:
            key_data = json.load(f)
            self.email = key_data["email"]
            self.secret_key = key_data["secret_key"]

    def init_from_new_email(self):
        temp_email = TempMail()
        self.email = temp_email.email
        self._reg_new_user()
        for i in range(5):
            _id = temp_email.get_email_id_from_subject("Activate your cutout.pro account")
            if _id:
                break
            sleep(2)
        else:
            # return
            self.init_from_new_email()

        _token = re.search(r'token=([^\s&]+)"', temp_email.get_email_content(_id)).group(1)

        self.user_activation(_token)

        self.save_local()

    def save_local(self):
        with open("key.json","w") as f:
            f.write(json.dumps({"email":self.email,"secret_key":self.secret_key}))

    def _reg_new_user(self):
        _mail = self.email.replace("@","%40")
        requests.get(CUTOUT_REG.format(email=_mail,password=self.email))

    def user_activation(self,token):
        res = requests.get(CUTOUT_ACTIVATION.format(token=token))
        self.token = res.json()["data"]["token"]
        self._update_secret_key()

    def _update_secret_key(self):
        res = requests.get(CUTOUT_SECRET_KEY,headers={"token":self.token})
        self.secret_key = res.json()["data"]

    def image_enhance(self,img_path,quality="jpg_100",save_path=None):
        print(f"enhancing {img_path}...")
        if save_path is None:
            _dir, _file = os.path.split(img_path)
            _file = f"enhanced_{_file.split('.')[0]}.png"
            save_path = os.path.join(_dir,_file)
        response = requests.post(
            CUTOUT_IMAGE_ENHANCE.format(format=quality),
            files={'file': open(img_path, 'rb')},
            headers={'APIKEY': self.secret_key}
        )
        if self.check_it_failed(response):
            self.image_enhance(img_path,quality=quality,save_path=save_path)
        else:
            with open(save_path, 'wb') as out:
                out.write(response.content)
            return save_path

    def background_remove(self,img_path,save_path=None):
        print(f"background remove {img_path}...")
        if save_path is None:
            _dir, _file = os.path.split(img_path)
            _file = f"nobg_{_file.split('.')[0]}.png"
            save_path = os.path.join(_dir, _file)
        response = requests.post(
            CUTOUT_BACKGROUND_REMOVE,
            files={'file': open(img_path, 'rb')},
            headers={'APIKEY': self.secret_key}
        )
        if self.check_it_failed(response):
            self.background_remove(img_path, save_path=save_path)
        else:
            with open(save_path, 'wb') as out:
                out.write(response.content)
        return save_path

    def check_it_failed(self,response):
        try:
            if response.json()["data"] == None:
                print(response.json())
                self.init_from_new_email()
                return True
        except:
            pass
        return False

    def download(self,img_path,enhance_quality,save_path):
        _dir, _file = os.path.split(save_path)
        _file = f"nobg_{_file.split('.')[0]}.png"
        bg_path = os.path.join(_dir, _file)
        _bg = self.background_remove(img_path, bg_path)
        if enhance_quality:
            _enh = self.image_enhance(img_path,quality=enhance_quality, save_path=save_path)
        else:
            _enh = img_path
        return _bg, _enh