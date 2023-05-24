import json
import os

import requests

NEW_EMAIL = "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1"
INBOX_LIST = "https://www.1secmail.com/api/v1/?action=getMessages&login={username}&domain={domain}"
READ_EMAIL = "https://www.1secmail.com/api/v1/?action=readMessage&login={username}&domain={domain}&id={email_id}"

class TempMail:
    def __init__(self,email=None):
        self.email = email or requests.get(NEW_EMAIL).json()[0]
        self.username, self.domain = self.email.split("@")

    def inbox(self):
        inbox_list  = requests.get(INBOX_LIST.format(username=self.username,domain=self.domain)).json()
        return inbox_list

    def get_email_id_from_subject(self,subject):
        for email in self.inbox():
            if email["subject"] == subject:
                return email['id']
        return None

    def get_email_content(self,email_id):
        print(email_id)
        url = READ_EMAIL.format(username=self.username,domain=self.domain,email_id=email_id)
        print(url)
        return requests.get(url).json()["body"]