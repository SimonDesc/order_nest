# Imports standard de Python
import io
import os.path

# Imports Django
from django.conf import settings
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

# Bibliothèques tierces
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# Imports relatifs à l'application
from ..forms import NewOrderForm, NewCustomerForm
from ..models import Customer, Order, OrderHasProduct, OrderAttachment
from .api import DeleteOrderAttachment


def print_pdf(request, pk):
    """
    The function `print_pdf` generates a PDF ticket with order details and a company logo, and then
    returns it as a downloadable file.

    :param request: The `request` parameter in the `print_pdf` function is typically used to handle
    incoming HTTP requests in Django views. It contains metadata about the request, such as headers,
    user information, and the requested URL. In this specific function, the `request` parameter is not
    being used directly, but
    :param pk: The `pk` parameter in the `print_pdf` function is used to identify a specific order by
    its primary key (pk) in the database. This primary key is used to retrieve the order details and
    generate a PDF ticket for that particular order
    :return: The code is returning a PDF file as an attachment named "ticket.pdf" containing the details
    of a specific order from the database. The PDF includes a header with a logo and title, a body
    section with information about the order, and a footer with contact details.
    """
    # Vérification et récupération de la commande
    if pk:
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return HttpResponse("<h1>Commande non trouvée</h1>")

    buf = io.BytesIO()
    page_width, page_height = 155, 160  # Dimensions ajustées de la page
    c = canvas.Canvas(buf)
    c.setPageSize((page_width, page_height))

    # HEADER
    logo_path = finders.find("img/logo_galerie.jpg")
    logo_height = 30  # Hauteur du logo
    logo_width = 50  # Largeur du logo
    c.drawImage(
        logo_path,
        10,
        page_height - logo_height - 10,
        width=logo_width,
        height=logo_height,
    )

    # TITLE
    title_y_position = page_height - logo_height - 0
    c.setFont("Helvetica-Bold", 9)
    c.drawString(64, title_y_position, "Galerie Libre Cours")

    # BODY
    text_start_y_position = title_y_position - 22
    textob = c.beginText(10, text_start_y_position)
    c.setFont("Helvetica", 9)

    # Calculer le total pour chaque produit
    product_order = OrderHasProduct.objects.filter(order=pk)
    for product in product_order:
        product.total = product.product.selling_price_unit * 1
    total_order = sum(product.total for product in product_order)

    if total_order != 0:
        lines = [
            f"Date de création: {order.created_at.strftime('%d/%m/%Y')}",
            f"Commande: {str(pk)}",
            f"Client: {order.customer.first_name} {order.customer.last_name}",
            f"Prix: {total_order} €",
        ]
    else:
        lines = [
            f"Date de création: {order.created_at.strftime('%d/%m/%Y')}",
            f"Commande: {str(pk)}",
            f"Client: {order.customer.first_name} {order.customer.last_name}",
        ]

    line_height = 3  # espace entre les lignes

    for line in lines:
        textob.textLine(line)
        textob.moveCursor(0, line_height)

    c.drawText(textob)

    # FOOTER
    footer_text_line1 = "50 Rue de Dreuilhe, 31250 Revel"
    footer_text_line2 = "05 62 18 91 84 / 06 50 80 77 23"
    footer_text_x_position = 10
    footer_text_y_position = 30
    c.setFont("Helvetica", 7)
    c.drawString(footer_text_x_position, footer_text_y_position, footer_text_line1)
    line_height = 10
    footer_text_y_position2 = footer_text_y_position - line_height
    c.drawString(footer_text_x_position, footer_text_y_position2, footer_text_line2)

    c.showPage()
    c.save()
    buf.seek(0)

    return FileResponse(buf, as_attachment=True, filename="ticket.pdf")


class CreateOrder(CreateView):
    """
    The `CreateOrder` class in Python defines a view for creating orders and associated customers,
    handling form data validation and processing.
    """

    form_class = NewOrderForm
    template_name = "webapp/orders/order-create.html"
    success_url = "/dashboard"

    def get_context_data(self, **kwargs):
        """
        The function `get_context_data` returns a dictionary containing instances of `NewOrderForm` and
        `NewCustomerForm`.
        :return: A dictionary named `context` is being returned, which contains two key-value pairs. The
        keys are "order_form" and "customer_form", and the values are instances of the `NewOrderForm` and
        `NewCustomerForm` classes, respectively.
        """
        context = {
            "order_form": NewOrderForm(),
            "customer_form": NewCustomerForm(),
        }

        return context

    def get_or_create_customer(self, customer_id, customer_form):
        """
        The function `get_or_create_customer` takes a customer ID and a customer form, attempts to retrieve
        an existing customer based on the ID, and creates a new customer if no existing customer is found.

        :param customer_id: The `customer_id` parameter is the unique identifier for a customer. It is used
        to retrieve an existing customer from the database if it exists, or to create a new customer if no
        customer with that ID is found
        :param customer_form: The `customer_form` parameter in the `get_or_create_customer` method is likely
        an instance of a form class that is used to create or update customer information. This form would
        typically contain fields and validation rules for customer data such as name, email, address, etc.
        When calling the `save
        :return: The function `get_or_create_customer` returns a tuple containing two values: the customer
        object and a boolean indicating whether the customer is an existing customer or a newly created one.
        """
        is_existing_customer = False
        customer = None

        # On test l'id
        try:
            customer_id = int(customer_id)
        except ValueError:
            customer_id = None
        # Si on a un id valide
        if customer_id:
            try:
                # on essaye de le récupérer (s'il existe)
                customer = Customer.objects.get(id=customer_id)
                is_existing_customer = True
            except Customer.DoesNotExist:
                customer = None
        # Si on a pas d'id valide, on créer un nouveau client
        if not customer:
            customer = customer_form.save()
        return customer, is_existing_customer

    def post(self, request, *args, **kwargs):
        """
        This Python function processes form data to create or update an order and its associated customer.

        :param request: The `request` parameter in the `post` method is an HttpRequest object that
        represents the HTTP request made by the user. It contains information about the request, such as the
        request method (GET, POST, etc.), headers, user data, and any data sent in the request body (e.g
        :return: If both the order form and customer form are valid, the code returns a redirect to the edit
        page for the newly created order. If the forms are not valid, it returns a render of the current
        page with the order form, customer form, and customer ID in the context.
        """
        order_form = NewOrderForm(request.POST)
        customer_form = NewCustomerForm(request.POST)

        if order_form.is_valid() and customer_form.is_valid():
            # On récupère l'id du champ caché
            customer_id = request.POST.get("id", None)
            print(customer_id)
            # On récupère le client (existant ou nouveau)
            customer, is_existing_customer = self.get_or_create_customer(
                customer_id, customer_form
            )
            # Si c'est un nouveau client
            if is_existing_customer:
                # On boucle sur les données du formulaire pour mettre à jour l'existant
                for field, value in customer_form.cleaned_data.items():
                    setattr(customer, field, value)
                customer.save()

            # On rattache le client à l'order
            order = order_form.save(commit=False)
            order.customer = customer
            order.save()
            redirect_url = f"/orders/{order.id}/edit/"
            return redirect(redirect_url)
        else:
            # Si le formulaire n'est pas valide
            # On renvoi le context + l'id du client
            customer_id = request.POST.get("id", None)
            context = {
                "order_form": order_form,
                "customer_form": customer_form,
                "customer_id": customer_id,
            }
            return render(request, self.template_name, context)


class EditOrder(UpdateView):
    model = Order
    form_class = NewOrderForm
    template_name = "webapp/orders/order-edit.html"
    success_url = reverse_lazy("webapp:dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context["order_form"] = NewOrderForm(instance=order)
        customer_instance = order.customer
        context["customer_form"] = NewCustomerForm(instance=customer_instance)
        context["product_order"] = OrderHasProduct.objects.filter(order=order.id)
        context["attachments"] = OrderAttachment.objects.filter(
            order=order.id, type="canvas"
        )[:50]
        context["attachments_pictures"] = [
            {
                "filename": os.path.basename(attachment.file.name),
                "url": attachment.file.url,
                "pk": attachment.pk,
            }
            for attachment in OrderAttachment.objects.filter(
                order=order.id, type="picture"
            ).order_by("pk")[:50]
        ]
        return context

    # Check la validité de form (order)
    def form_valid(self, form):
        # Check la validité de customer
        customer_form = NewCustomerForm(
            self.request.POST, instance=self.object.customer
        )
        if customer_form.is_valid():
            form.save()
            customer_form.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        customer_form = NewCustomerForm(
            self.request.POST, instance=self.object.customer
        )
        context = self.get_context_data()
        context["customer_form"] = customer_form
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        # Sauvegarder le referer dans la session lors du premier chargement de la page
        self.request.session["referer"] = self.request.META.get(
            "HTTP_REFERER", reverse_lazy("webapp:dashboard")
        )
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        # Utiliser l'URL de la session ou une URL par défaut
        return self.request.session.get("referer", reverse_lazy("webapp:dashboard"))


class DeleteOrder(DeleteView):
    model = Order
    context_object_name = "commandes"
    template_name = "webapp/orders/order-delete.html"
    success_url = reverse_lazy("webapp:dashboard")

    # Surcharge de la méthode afin de supprimer les medias(canvas+photos)
    def form_valid(self, form):
        order_id = self.object.id
        # Trouver toutes les pièces jointes associées à cette commande
        order_attachments = OrderAttachment.objects.filter(order=order_id)

        for attachment in order_attachments:
            # Créer une instance de DeleteOrderAttachment
            delete_attachment_view = DeleteOrderAttachment()
            delete_attachment_view.object = attachment
            delete_attachment_view.request = self.request
            delete_attachment_view.kwargs = {
                "pk": attachment.pk
            }  # Passer l'identifiant de l'objet

            # Appeler la méthode delete de DeleteOrderAttachment
            delete_attachment_view.delete(self.request)

        response = super().form_valid(form)
        return response


class SearchOrder(ListView):
    model = Order
    template_name = "webapp/orders/order-search.html"

    def get_queryset(self):
        query = self.request.GET.get("q")
        order_list = Order.objects.filter(
            Q(label__icontains=query)  # libellé
            | Q(status__label__icontains=query)  # status
            | Q(pk__icontains=query)  # id
            | Q(customer__first_name__icontains=query)
            | Q(customer__last_name__icontains=query)
            | Q(customer__mail__icontains=query)
            | Q(customer__address__icontains=query)
            | Q(customer__phone_number__icontains=query)
        )[:50]
        return order_list
