# Imports standard de Python
from typing import Any

# Imports Django
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField, Q, Prefetch, Count
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView

# Imports relatifs à l'application
from ..forms import NewCustomerForm
from ..models import Order, Customer, OrderAttachment


class WebappHome(ListView):
    """
    The `WebappHome` class in the Python code snippet retrieves and displays a list of orders with
    specific statuses, annotated with priority values and prefetched attachments, for a web application
    home page.
    """
    model = Order
    template_name = "webapp/home.html"
    context_object_name = "orders"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        The `get_context_data` method in the Python code snippet retrieves context data including verbose
        names for fields in Order and Customer models.
        
        :param : The `get_context_data` method is used to add additional context data to be used in the
        template rendering process. In this case, it is adding verbose names for fields in the `Order` and
        `Customer` models
        :type : Any
        :return: The `get_context_data` method is returning a dictionary containing two key-value pairs:
        1. "verbose_names": A dictionary mapping field names to their verbose names for the `Order` model.
        2. "customer_verbose_names": A dictionary mapping field names to their verbose names for the
        `Customer` model.
        """
        context = super().get_context_data(**kwargs)
        context["verbose_names"] = {
            field.name: field.verbose_name
            for field in Order._meta.get_fields()
            if hasattr(field, "verbose_name")
        }
        context["customer_verbose_names"] = {
            field.name: field.verbose_name
            for field in Customer._meta.get_fields()
            if hasattr(field, "verbose_name")
        }
        return context

    def get_queryset(self):
        """
        The function `get_queryset` retrieves a queryset of orders with specific statuses, annotated with
        priority values and prefetched attachments, ordered by priority and creation date.
        :return: The `get_queryset` method is returning a queryset of Order objects with the following
        criteria:
        1. Annotating each Order object with a priority field based on the status field. If the status is
        "Urgent", priority is set to 1, otherwise default priority is set to 2.
        2. Filtering the Order objects to include only those with status "En cours" or "U
        """
        attachments = OrderAttachment.objects.all()
        queryset = (
            Order.objects
            .annotate(
                priority=Case(
                    When(status="Urgent", then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .filter(Q(status="En cours") | Q(status="Urgent"))
            .prefetch_related(Prefetch("attachments", queryset=attachments))
            .order_by("priority", "-created_at")[:20]
        )
        return queryset


class CustomerView(ListView):
    """
    The `CustomerView` class is a list view for displaying customer data in a web application.
    """
    model = Customer
    template_name = "webapp/customers/customer.html"
    context_object_name = "customers"


class EditCustomer(UpdateView):
    """
    This Python class `EditCustomer` extends `UpdateView` to edit customer details and includes a method
    to calculate and display a summary of orders based on their status.
    """
    model = Customer
    form_class = NewCustomerForm
    template_name = "webapp/customers/customer-edit.html"
    success_url = reverse_lazy("webapp:customer")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        The function `get_context_data` retrieves context data for a customer object and calculates the
        summary of orders based on their status.
        
        :param : In the provided code snippet, a method `get_context_data` is defined within a class. This
        method is used to retrieve additional context data for a view in a Django application. Here's an
        explanation of the code:
        :type : Any
        :return: The `get_context_data` method is returning a dictionary `context` that contains the summary
        of orders for a specific customer. The summary includes the counts of orders based on different
        statuses such as 'En cours', 'En attente', 'Urgent', 'Terminée', 'Annulée', and 'Facturée'. These
        counts are stored in the `orders_summary` dictionary and
        """
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        
        # Compter les orders selon leur statut
        orders_summary = Order.objects.filter(customer=customer).aggregate(
            total_in_progress=Count('pk', filter=Q(status__in=['En cours', 'En attente', 'Urgent'])),
            total_ended=Count('pk', filter=Q(status__in=['Terminée', 'Annulée'])),
            total_invoice=Count('pk', filter=Q(status='Facturée'))
        )

        context.update(orders_summary)
        return context


class Dashboard(ListView):
    """
    The `Dashboard` class in Python defines a ListView for displaying orders with pagination and
    calculates various counts related to different statuses and payments of orders for display in a
    context dictionary.
    """
    paginate_by = 20
    model = Order
    template_name = "webapp/dashboard.html"
    context_object_name = "orders"
    ordering = ["-id"]

    def get_context_data(self, **kwargs):
        """
        The function `get_context_data` retrieves and calculates various counts related to different
        statuses of orders for display in a context dictionary.
        :return: The `get_context_data` method is returning a context dictionary containing various counts
        and information related to different statuses and payments of orders. The context includes the total
        number of objects, the number of objects in different statuses such as "En cours", "Terminée", "En
        attente", "Facturée", "Annulée", "Urgent", and the number of objects with payment
        """
        context = super().get_context_data(**kwargs)
        page_number = context["page_obj"].number
        element_by_page = self.paginate_by

        all_objects = Order.objects.all()

        progress_objects = Order.objects.filter(status="En cours")
        count_progress = progress_objects.count()

        ended_orders = Order.objects.filter(status="Terminée")
        count_ended = ended_orders.count()

        waiting_objects = Order.objects.filter(status="En attente")
        count_waiting = waiting_objects.count()

        invoice_objects = Order.objects.filter(status="Facturée")
        count_invoice = invoice_objects.count()

        canceled_objects = Order.objects.filter(status="Annulée")
        count_canceled = canceled_objects.count()

        urgent_objects = Order.objects.filter(status="Urgent")
        count_urgent = urgent_objects.count()

        payment_objects = Order.objects.filter(payment="Réglé")
        count_urgent = urgent_objects.count()

        count_all = Paginator(all_objects, element_by_page)
        context["total_obj"] = count_all.count

        accumulated_objects = (page_number - 1) * element_by_page + len(
            context["page_obj"]
        )

        context["accumulated_objects"] = accumulated_objects
        context["count_progress"] = count_progress
        context["count_ended"] = count_ended
        context["count_waiting"] = count_waiting
        context["count_invoice"] = count_invoice
        context["count_canceled"] = count_canceled
        context["count_urgent"] = count_urgent

        context["count_payment"] = count_urgent

        return context
