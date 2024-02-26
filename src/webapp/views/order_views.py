from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from ..forms import NewOrderForm, NewCustomerForm
from ..models import Customer, Order, OrderHasProduct, OrderAttachment
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
import os.path
from django.conf import settings
from django.db.models import Q
from .api_views import DeleteOrderAttachment

# PDF
from django.contrib.staticfiles import finders
from reportlab.pdfgen import canvas
import io
from django.http import FileResponse, HttpResponse
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

def print_pdf(request, pk):
    # Vérification et récupération de la commande
    if pk:
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return HttpResponse('<h1>Commande non trouvée</h1>')

    buf = io.BytesIO()
    page_width, page_height = 155, 160  # Dimensions ajustées de la page
    c = canvas.Canvas(buf)
    c.setPageSize((page_width, page_height))
    
    # HEADER
    logo_path = finders.find('img/logo_galerie.jpg')
    logo_height = 30  # Hauteur du logo
    logo_width = 50  # Largeur du logo
    c.drawImage(logo_path, 10, page_height - logo_height - 10, width=logo_width, height=logo_height)
    
    # TITLE
    title_y_position = page_height - logo_height - 0
    c.setFont("Helvetica-Bold", 9)
    c.drawString(64, title_y_position, "Galerie Libre Cours")
    
    # BODY
    text_start_y_position = title_y_position - 22
    textob = c.beginText(10, text_start_y_position)
    c.setFont("Helvetica", 9)
    
    lines = [
        f"ID Commande: {str(pk)}",
        f"Libellé: {order.label}",
        f"Prénom: {order.customer.first_name}",
        f"Nom: {order.customer.last_name}",
        f"Téléphone: {str(order.customer.formatted_phone_number())}",
    ]

    line_height = 3  # espace entre les lignes

    for line in lines:
        textob.textLine(line)
        textob.moveCursor(0, line_height)

    c.drawText(textob)
    
    # FOOTER
    footer_text_line1 = "50 Rue de Dreuilhe, 31250 Revel"
    footer_text_line2 = "05 62 18 91 84"
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
    form_class = NewOrderForm
    template_name = "webapp/orders/order-create.html"
    success_url = "/dashboard"

    def get_context_data(self, **kwargs):
        context = {
            "order_form": NewOrderForm(),
            "customer_form": NewCustomerForm(),
        }

        return context

    def get_or_create_customer(self, customer_id, customer_form):
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
