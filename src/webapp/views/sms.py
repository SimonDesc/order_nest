# Bibliothèques standard
import http.client
import json

# Bibliothèques tierces
import environ
import requests

# Imports Django
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

# Imports relatifs à l'application
from ..models import Customer, Order

env = environ.Env()
environ.Env.read_env()


def get_credit_sms(request):
    """
    The function `get_credit_sms` makes a request to an SMS API to retrieve credit information and
    returns a JSON response based on the API's success status.
    
    :param request: The `request` parameter in the `get_credit_sms` function is typically a Django
    HttpRequest object that represents the HTTP request made by the client to the server. It contains
    information about the request, such as the request method, headers, and data. In this function, the
    `request` parameter is
    :return: The `get_credit_sms` function returns a JSON response containing information about the SMS
    credit balance. If the API request is successful, it returns a JSON response with the success status
    and the data received from the API. If there is an error or the API request is not successful, it
    returns a JSON response with the success status set to False and an error message indicating that an
    error occurred.
    """
    API_KEY = env("SMS_API")
    URL = "https://api.smspartner.fr/v1"

    url = URL + "/me?apiKey=" + API_KEY
    r = requests.get(url)
    r_json = r.json()

    if r_json.get("success") == True:
        response = JsonResponse({"success": True, "data": r_json})
    else:
        response = JsonResponse(
            {"success": False, "error": "Une erreur s'est produite."}
        )

    return response


def send_sms(request):
    """
    The `send_sms` function sends an SMS message using the SMSPartner API with the provided content and
    phone number.
    
    :param request: The `send_sms` function you provided seems to be a Django view that sends an SMS
    using the SMSPartner API. Let me explain the parameters used in the function:
    :return: A `JsonResponse` containing the dictionary `data_dict` is being returned from the
    `send_sms` function.
    """
    content = request.GET.get("content", "")
    phone_number = request.GET.get("phone_number", "")
    
   
    conn = http.client.HTTPSConnection("api.smspartner.fr")

    payload = json.dumps(
        {
            "apiKey": env("SMS_API"),
            "phoneNumbers": phone_number,
            "sender": "LibreCours",
            "gamme": 1,
            "message": content,
            "webhookUrl": env("WEB_HOOK"),
        }
    )

    headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
        "cache-control": "no-cache",
    }

    conn.request(
        "POST", "/v1/send", payload, headers
    )  # Une requête POST est envoyée au serveur SMSPartner avec le chemin d'URL "/v1/send"

    res = conn.getresponse()  # La réponse est ensuite stockée dans la variable res.
    # Lire et décoder le contenu de la réponse
    data = res.read().decode("utf-8")

    # Convertir la chaîne JSON en dictionnaire Python
    data_dict = json.loads(data)

    # Retourner une JsonResponse avec le dictionnaire
    return JsonResponse(data_dict)


def modal_sms(request, pk):
    order = get_object_or_404(Order, pk=pk)
    context = {"order": order}
    return render(request, "webapp/sms/order-sms.html", context)


def modal_sms_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {"customer": customer}
    return render(request, "webapp/sms/order-sms-customer.html", context)
