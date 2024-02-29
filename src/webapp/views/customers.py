# Imports Django
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView

# Imports relatifs à l'application
from ..forms import NewCustomerForm
from ..models import Customer


def autocomplete(request):
    """
    The `autocomplete` function retrieves a list of active customers matching a given query and formats
    the results for autocomplete suggestions.
    
    :param request: The `autocomplete` function takes a request object as a parameter. The function
    retrieves the query string parameter "term" from the GET parameters of the request. It then filters
    the Customer objects based on the query string, specifically searching for matching first names or
    last names that contain the query string while also ensuring
    :return: A JSON response containing a list of up to 10 customer objects that match the search query
    provided in the request. Each customer object includes the ID, first name, last name, phone number,
    address, email, comments, and a label combining the first and last name.
    """
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
    """
    The function `get_customers` retrieves and paginates customer data based on search criteria from a
    request in a Django web application.
    
    :param request: The `get_customers` function you provided is a view function in Django that
    retrieves a list of customers based on search criteria and returns the results in a paginated JSON
    response
    :return: A JSON response containing a list of customer details based on the search query and
    pagination parameters. The response includes customer's last name, first name, phone number, email,
    and a URL for editing the customer. Additionally, the total count of customers matching the search
    criteria is included in the response.
    """
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


def deactivate_customer(request, pk):
    """
    The `deactivate_customer` function deactivates a customer by setting their active status to False in
    the database and returns a JSON response indicating the success or failure of the operation.
    
    :param request: The `request` parameter in the `deactivate_customer` function is expected to be an
    HTTP request object that contains information about the incoming request, such as the request method
    (GET, POST, etc.), headers, and data. In this context, the function is checking if the request
    method is not
    :param pk: The `pk` parameter in the `deactivate_customer` function stands for the primary key of
    the customer that you want to deactivate. It is used to uniquely identify the customer in the
    database
    :return: The `deactivate_customer` function returns a JSON response with a status and message based
    on different scenarios.
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


class CreateCustomer(CreateView):
    """
    The `CreateCustomer` class is a Django view for creating new customer instances with a specified
    form and template.
    """
    model = Customer
    form_class = NewCustomerForm
    template_name = "webapp/customers/customer-create.html"
    success_url = reverse_lazy("webapp:customer")
