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
from reportlab.pdfgen import canvas
import io
from django.http import FileResponse, HttpResponse
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

def print_pdf(request, pk):
    # On vérifie si un identifiant de commande est fourni
    if pk:
        try:
            # Tentative de récupération de la commande
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            # Si la commande n'existe pas, on retourne une erreur HTTP
            return HttpResponse('<h1>Commande non trouvée</h1>')

    # Création d'un tampon de flux en mémoire
    buf = io.BytesIO()
    # Création d'un canevas pour le PDF avec orientation de la page du bas vers le haut
    c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
    # Initialisation d'un objet texte
    textob = c.beginText()
    textob.setTextOrigin(inch, 0.5 * inch)  # Définit l'origine du texte avec une marge
    textob.setFont("Helvetica", 12)  # Choix de la police et taille

    # Préparation des lignes à afficher
    lines = [
        f"ID Commande: {str(pk)}",
        f"Libellé: {order.label}",
        f"Prénom: {order.customer.first_name}",
        f"Nom: {order.customer.last_name}",
        f"Téléphone: {str(order.customer.formatted_phone_number())}",
    ]

    # Définition de l'espace entre les lignes
    line_height = 14

    for line in lines:
        textob.textLine(line)  # Ajout de la ligne au document
        textob.moveCursor(0, line_height)  # Déplacement du curseur pour l'espace entre les lignes

    # Finalisation de l'écriture sur le document
    c.drawText(textob)
    c.showPage()
    c.save()
    buf.seek(0)

    # Retourne le PDF comme réponse de fichier
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
