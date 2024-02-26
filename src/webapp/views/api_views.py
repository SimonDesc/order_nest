import re
import time
import os.path
import imghdr
import environ

# SMS
import http.client
import json


from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import (
    DeleteView,
)
from ..models import Customer, Order, OrderAttachment
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from .utils import delete_file_from_s3

import requests

env = environ.Env()
environ.Env.read_env()


def get_clients(request):
    query = request.GET.get("term", "")
    clients = Customer.objects.filter(
        (Q(first_name__icontains=query) | Q(last_name__icontains=query))
        & Q(active=True)
    ).values(
        "id", "first_name", "last_name", "phone_number", "address", "mail", "comments"
    )[
        :10
    ]

    results = []
    for client in clients:
        client_dict = {
            "id": client["id"],
            "first_name": client["first_name"],
            "last_name": client["last_name"],
            "phone_number": str(client["phone_number"]),
            "address": client["address"],
            "mail": client["mail"],
            "comments": client["mail"],
            "label": f"{client['first_name']} {client['last_name']}",
        }
        results.append(client_dict)

    return JsonResponse(results, safe=False)


def get_customers(request):
    search_query = request.GET.get("search", "")

    # base de la requête
    customers_query = Customer.objects.filter(active=True)

    if search_query:
        customers_query = Customer.objects.filter(
            Q(last_name__icontains=search_query) | Q(first_name__icontains=search_query)
        )

    # Calculer le total avant la pagination
    total = customers_query.count()

    # Pagination
    page = int(request.GET.get("page", 1))
    size = int(request.GET.get("size", 20))
    offset = size * page
    customers_query = customers_query.order_by("-id")[offset : offset + size]

    # Construction de la liste de résultats
    order_list = [
        {
            "last_name": str(customer.last_name),
            "first_name": str(customer.first_name),
            "phone_number": str(customer.formatted_phone_number()),
            "mail": str(customer.mail),
            "url": str(reverse("webapp:customer-edit", kwargs={"pk": customer.pk})),
        }
        for customer in customers_query
    ]

    data = {
        "results": order_list,
        "total": total,
    }

    return JsonResponse(data)


def get_orders(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    customer_id = request.GET.get("customerId", "")

    # base de la requête
    orders_query = Order.objects.all()

    if search_query:
        orders_query = Order.objects.filter(
            Q(customer__last_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
        )

    if status_filter:
        status_filter_list = status_filter.split(",")
        orders_query = orders_query.filter(status__in=status_filter_list)

    if customer_id:
        orders_query = orders_query.filter(customer__id=customer_id)

    # Calculer le total avant la pagination
    total = orders_query.count()

    # Pagination
    page = int(request.GET.get("page", 1))
    size = int(request.GET.get("size", 20))
    offset = size * page
    orders_query = orders_query.order_by("-id")[offset : offset + size]

    # Construction de la liste de résultats
    order_list = [
        {
            "IDorder": str(order.pk),
            "customer": (
                str(order.customer.last_name + " " + order.customer.first_name)[:20]
                + "..."
                if len(str(order.customer.last_name + " " + order.customer.first_name))
                > 19
                else str(order.customer.last_name + " " + order.customer.first_name)[
                    :20
                ]
            ),
            "label": str(order.label)[:30],
            "status": str(order.status),
            "created": order.created_at.strftime("%Y-%m-%d"),
            "payment": str(order.payment),
            "url": str(reverse("webapp:order-edit", kwargs={"pk": order.pk})),
        }
        for order in orders_query
    ]

    data = {
        "results": order_list,
        "total": total,
    }

    return JsonResponse(data)


def is_allowed_extension(filename):
    """
    Vérifie si l'extension du fichier est autorisée.
    """
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


def clean_filename(filename):
    """
    Nettoie le nom de fichier en remplaçant les caractères spéciaux.
    """
    name, ext = os.path.splitext(filename)
    # Remplacer tous les caractères non alphanumériques (sauf le point de l'extension) par des underscores
    name = re.sub(r"[^\w]", "_", name)
    return f"{name}{ext}"


def unique_file_name(original_name, order_id):
    """
    Génère un nom de fichier unique en utilisant un UUID et un horodatage.
    """
    basename, ext = os.path.splitext(original_name)
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    return f"{basename}_{order_id}_{timestamp}{ext}"


def save_attachment(request):
    """
    Traite et sauvegarde un fichier en tant qu'OrderAttachment.
    Gère les fichiers 'canvas' et 'picture'.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Méthode non autorisée"}, status=405
        )

    try:

        order_id = request.POST.get("orderId")
        if not order_id:
            raise ValueError("L'ID de commande est requis.")

        try:
            order = Order.objects.get(pk=order_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Commande introuvable"}, status=404
            )

        file = request.FILES.get("img")
        if file:
            # Nettoyer le nom de fichier
            cleaned_name = clean_filename(file.name)

            # Vérification de la taille du fichier
            max_size = 5 * 1024 * 1024  # 5MB
            if file.size > max_size:
                raise ValueError("Le fichier est trop volumineux.")

            # Vérification du type de fichier
            if imghdr.what(file) not in ["jpeg", "jpg", "png", "gif"]:
                raise ValueError("Type de fichier non pris en charge.")

            # Vérifier l'extension autorisée
            if not is_allowed_extension(cleaned_name):
                raise ValueError("Type de fichier non autorisé.")

            unique_name = unique_file_name(cleaned_name, order_id)

            drawing_data = request.POST.get("drawingData")
            attachment = OrderAttachment(order=order)
            if drawing_data:
                attachment.canvas_json = drawing_data
                attachment.type = "canvas"
            else:
                attachment.type = "picture"

            attachment.file.save(unique_name, file, save=True)

        else:
            raise ValueError("Aucun fichier fourni.")

        attachment.save()

        if attachment.type == "canvas":
            return HttpResponse(attachment.file.name)
        else:
            return JsonResponse(
                {
                    "status": "success",
                    "filename": {
                        "pk": attachment.pk,
                        "url": attachment.file.url,
                        "name": os.path.basename(attachment.file.name)[0:20],
                    },
                }
            )

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except PermissionDenied:
        return JsonResponse(
            {"status": "error", "message": "Permission refusée"}, status=403
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Erreur interne du serveur"}, status=500
        )


def get_canvas(request, pk):
    order = OrderAttachment.objects.filter(order_id=pk, type="canvas")[:50]
    for e in order.all():
        file_json = e.canvas_json

    if order:
        return JsonResponse({"exit": True, "json_file": file_json})
    return HttpResponse(False)


def deactivate_customer(request, pk):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Méthode non autorisée"}, status=405
        )

    try:
        customer = Customer.objects.get(pk=pk)
        customer.active = False
        customer.save()

        return JsonResponse(
            {"status": "success", "message": "Client désactivé avec succès"}
        )

    except Customer.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Client non trouvé"}, status=404
        )
    except PermissionDenied:
        return JsonResponse(
            {"status": "error", "message": "Permission refusée"}, status=403
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Erreur interne du serveur"}, status=500
        )


class DeleteOrderAttachment(DeleteView):
    """
    Classe de vue générique pour supprimer un objet OrderAttachment.
    Cette vue est utilisée pour supprimer des fichiers liés à un OrderAttachment,
    que ce soit un 'Canvas' ou une 'Picture'.
    """

    model = OrderAttachment

    def get_success_url(self):
        """
        Retourne l'URL de redirection après une suppression réussie.
        Redirige vers la page d'édition de la commande associée.
        """
        order_id = self.object.pk
        return reverse("webapp:order-edit", args=[order_id])

    def delete(self, request, *args, **kwargs):
        """
        Surcharge la méthode delete pour supprimer le fichier associé
        à l'objet OrderAttachment avant de supprimer l'objet lui-même.
        """
        try:
            self.object = self.get_object()
            file_key = self.object.file.name

            if delete_file_from_s3(file_key):
                self.object.delete()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse({"error": "Erreur de suppression du fichier S3."})
            # # Supprime le fichier si il existe dans le dossier MEDIA_ROOT
            # if self.object.file:
            #     file_path = os.path.join(settings.MEDIA_ROOT, self.object.file.path)
            #     if os.path.exists(file_path):
            #         os.remove(file_path)

            # Supprime l'objet OrderAttachment
            # self.object.delete()

            # Retourne une réponse JSON indiquant le succès de l'opération

        except OrderAttachment.DoesNotExist:
            return JsonResponse({"status": "Pièce jointe non trouvée"})


def get_credit_sms(request):
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

"""
todo: the api of sms partner doesn't permit to retrieve sms by phone number
I need to create a new table for storage all number and message id
"""
# def get_history_sms(request):
#     phone_number = request.GET.get("phone_number", "")
#     API_KEY = env("SMS_API")
#     URL = "https://api.smspartner.fr/v1"

#     # url = URL + "/message-status?apiKey=" + API_KEY + "&phoneNumber=" + phone_number 
    
#     data = {"apiKey":API_KEY,"SMSStatut_List":[{"phoneNumber":'0669171357'}]}
#     url = URL + '/multi-status'
    
#     r = requests.post(url, data=json.dumps(data), verify=False)
#     r_json = r.json()
#     print("R =====", r)
#     print(url)

#     if r_json.get("success") == True:
#         response = JsonResponse({"success": True, "data": r_json})
#     else:
#         response = JsonResponse(
#             {"success": False, "error": "Une erreur s'est produite."}
#         )

#     return response

def send_sms(request):
    content = request.GET.get("content", "")
    phone_number = request.GET.get("phone_number", "")
    
   
    conn = http.client.HTTPSConnection("api.smspartner.fr")

    payload = json.dumps(
        {
            "apiKey": env("SMS_API"),
            "phoneNumbers": phone_number,
            "sender": "Libre Cours",
            "gamme": 1,
            "message": content+':br:',
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
    return render(request, "webapp/orders/order-sms.html", context)


def modal_sms_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    context = {"customer": customer}
    return render(request, "webapp/orders/order-sms-customer.html", context)
