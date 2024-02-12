#!/usr/bin/python3

import http.client
import json
conn = http.client.HTTPSConnection("api.smspartner.fr")
print("début")
payload = json.dumps({
"apiKey": "4b7ce0bc008e9415bc4e5e5a03ba9ccc3e2be6ec", #remplacez par votre clé API SMSPartner
"phoneNumbers": "+33669171357", #remplacez par votre numéro de téléphone
"sender": "ORDERNEST",
"gamme": 1,
"message": "Cest un message test PYTHON", #remplacez par votre message
 "webhookUrl": "https://webhook.site/cc751c36-c958-4dc4-b006-2b8a537880ce" #remplacez TOKEN par votre token webhook.site
})
 
headers = {
'Content-Type': 'application/json',
'Content-Length': str(len(payload)),
'cache-control': 'no-cache'
}
 
conn.request("POST", "/v1/send", payload, headers) #Une requête POST est envoyée au serveur SMSPartner avec le chemin d'URL "/v1/send"
 
res = conn.getresponse() #La réponse est ensuite stockée dans la variable res.
 
data = res.read() 
 
print(data.decode("utf-8")) #Cette ligne lit les données de la réponse HTTP.
