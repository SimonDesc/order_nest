# Bibliothèques standard
import imghdr
import os.path

# Bibliothèques tierces
import environ

# Imports Django
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.generic import DeleteView

# Imports relatifs à l'application
from ..models import Customer, Order, OrderAttachment
from .utils import clean_filename, delete_file_from_s3, is_allowed_extension, unique_file_name

env = environ.Env()
environ.Env.read_env()


def get_orders(request):
    """
    The `get_orders` function retrieves and filters orders based on search query, status filter, and
    customer ID, then paginates the results and returns them in a JSON response.
    
    :param request: The `get_orders` function takes a `request` object as a parameter. This `request`
    object typically contains information about an HTTP request made to the server, including data sent
    via query parameters, form data, headers, etc
    :return: A JSON response containing a list of orders with specific details such as order ID,
    customer name, label, status, creation date, payment information, and URL for editing the order. The
    response also includes the total count of orders that match the search criteria.
    """
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    customer_id = request.GET.get("customerId", "")

    # base de la requête
    orders_query = Order.objects.all()

    if search_query:
        orders_query = Order.objects.filter(
            Q(customer__last_name__icontains=search_query)
            | Q(customer__first_name__icontains=search_query)
            | Q(id__exact=search_query)
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



def save_attachment(request):
    """
    The `save_attachment` function in Python handles saving attachments for orders, performing
    validations on the file size, type, and extension before saving it.
    
    :param request: The `save_attachment` function you provided is designed to handle saving attachments
    in a Django application. It expects a POST request with certain parameters such as "orderId", "img"
    (file), and "drawingData"
    :return: The `save_attachment` function returns a JSON response with different status messages and
    data depending on the outcome of the file saving process. Here are the possible return scenarios:
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
    """
    This function retrieves canvas data from OrderAttachment objects related to a specific order ID and
    returns it as a JSON response.
    
    :param request: The `request` parameter in the `get_canvas` function is typically an HttpRequest
    object that represents the current request from the client. It contains metadata about the request,
    such as headers, method, and user data. This parameter allows the function to access information
    about the current request being made to the server
    :param pk: The `pk` parameter in the `get_canvas` function represents the primary key of the order
    for which you want to retrieve the canvas information. It is used to filter the OrderAttachment
    objects based on the order_id field
    :return: The function `get_canvas` is returning a JSON response with the keys "exit" and "json_file"
    if the `order` variable is not empty. The value of "exit" is set to True, and the value of
    "json_file" is set to the `canvas_json` attribute of the last element in the `order` queryset. If
    the `order` variable is empty,
    """
    order = OrderAttachment.objects.filter(order_id=pk, type="canvas")[:50]
    for e in order.all():
        file_json = e.canvas_json

    if order:
        return JsonResponse({"exit": True, "json_file": file_json})
    return HttpResponse(False)


def deactivate_customer(request, pk):
    """
    The `deactivate_customer` function deactivates a customer by setting their active status to False in
    the database and returns a JSON response indicating the success or failure of the operation.
    
    :param request: The `request` parameter in the `deactivate_customer` function is typically an
    HttpRequest object that represents the HTTP request made by the client. It contains information
    about the request, such as the method used (GET, POST, etc.), headers, and data. In this function,
    we are checking if
    :param pk: The `pk` parameter in the `deactivate_customer` function stands for the primary key of
    the customer that you want to deactivate. It is used to uniquely identify the customer in the
    database
    :return: The `deactivate_customer` function returns a JSON response based on different scenarios:
    1. If the request method is not POST, it returns an error message with status code 405.
    2. If the customer with the specified primary key (pk) is found, it deactivates the customer, saves
    the changes, and returns a success message.
    3. If the customer with the specified primary key
    """
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
    The `DeleteOrderAttachment` class extends `DeleteView` to delete an `OrderAttachment` object and its
    associated file, with custom methods for success URL retrieval and file deletion.
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

        except OrderAttachment.DoesNotExist:
            return JsonResponse({"status": "Pièce jointe non trouvée"})
