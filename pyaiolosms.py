import requests
from modules.pylavor import remove_non_ascii

#I actually never tried this moude
#it would require me to create an account.. pff....
#it will prolly work, although the instructions were not really clear. bwo

class SmSender():
    def __init__(self, username, password):
        
        self.url = "https://www.smsapi.si/poslji-sms"
        self.username = username
        self.password = password
    
    def send_sms_SLO_number(self, number_to_send_to, msg):
        
        #clear a little bit the number
        number_to_send_to = number_to_send_to.strip().replace(" ", "")
        
        url_values = {'un': self.username,   #API usenrame
             'ps': self.password,            #API password
             'from': '031492148',            #senders number. no idea what this is, instructions no clearo
             'to': str(number_to_send_to),   #send to
             'cc': '386',                    #countrycode (386)
             'm': remove_non_ascii(str(msg))}                  #message
    
        response = requests.post(self.url, data = url_values).split("##")
        
        return response
