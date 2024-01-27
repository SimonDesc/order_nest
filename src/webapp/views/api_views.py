import re
import time
import os.path
import imghdr



from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.generic import (
    DeleteView,
)
from ..models import Customer, Order, OrderAttachment
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from .utils import delete_file_from_s3


def get_clients(request):
    query = request.GET.get("term", "")
    clients = Customer.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
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


def get_orders(request):
    search_query = request.GET.get('search', '')

    # Définir la base de la requête
    if search_query:
        orders_query = Order.objects.filter(
            Q(customer__last_name__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) 
        )
    else:
        orders_query = Order.objects.all()

    # Calculer le total avant la pagination
    total = orders_query.count()

    # Pagination
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 20))
    offset = size * page
    orders_query = orders_query.order_by("-id")[offset:offset + size]

    # Construction de la liste de résultats
    order_list = [
        {
            "IDorder": str(order.pk),
            "customer": str(order.customer.last_name + " " + order.customer.first_name)[:20] + "..." if len(str(order.customer.last_name + " " + order.customer.first_name)) > 19 else str(order.customer.last_name + " " + order.customer.first_name)[:20],
            "label": str(order.label)[:30],
            "status": str(order.status),
            "created": order.created_at.strftime("%d/%m/%Y"),
            "payment": str(order.payment),
            "url": str(reverse("webapp:order-edit", kwargs={"pk": order.pk})),
        } for order in orders_query
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
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


def clean_filename(filename):
    """
    Nettoie le nom de fichier en remplaçant les caractères spéciaux.
    """
    name, ext = os.path.splitext(filename)
    # Remplacer tous les caractères non alphanumériques (sauf le point de l'extension) par des underscores
    name = re.sub(r'[^\w]', '_', name)
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
        return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

    try:
        
        order_id = request.POST.get('orderId')
        if not order_id:
            raise ValueError("L'ID de commande est requis.")

        try:
            order = Order.objects.get(pk=order_id)
        except ObjectDoesNotExist:
            return JsonResponse({"status": "error", "message": "Commande introuvable"}, status=404)

        file = request.FILES.get('img')
        if file:
            # Nettoyer le nom de fichier
            cleaned_name = clean_filename(file.name)
            
            # Vérification de la taille du fichier
            max_size = 5 * 1024 * 1024  # 5MB
            if file.size > max_size:
                raise ValueError("Le fichier est trop volumineux.")

            # Vérification du type de fichier
            if imghdr.what(file) not in ['jpeg', 'jpg', 'png', 'gif']:
                raise ValueError("Type de fichier non pris en charge.")
     
            # Vérifier l'extension autorisée
            if not is_allowed_extension(cleaned_name):
                raise ValueError("Type de fichier non autorisé.")

            unique_name = unique_file_name(cleaned_name, order_id)
            
            drawing_data = request.POST.get('drawingData')
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
        return JsonResponse({"status": "error", "message": "Permission refusée"}, status=403)
    except Exception as e:
        return JsonResponse({"status": "error", "message": "Erreur interne du serveur"}, status=500)
    




def get_canvas(request, pk):
    order = OrderAttachment.objects.filter(order_id=pk, type="canvas")[:50]
    for e in order.all():
        file_json = e.canvas_json

    if order:
        return JsonResponse({"exit": True, "json_file": file_json})
    return HttpResponse(False)


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
        try :
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



