from typing import Any
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.views.generic import (
    ListView,
)
from ..models import Order, Customer, OrderAttachment


class WebappHome(ListView):
    model = Order
    template_name = "webapp/home.html"
    context_object_name = "orders"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['verbose_names'] = {field.name: field.verbose_name for field in Order._meta.get_fields() if hasattr(field, 'verbose_name')}
        context['customer_verbose_names'] = {field.name: field.verbose_name for field in Customer._meta.get_fields() if hasattr(field, 'verbose_name')}
        return context

    def get_queryset(self):
        attachments = OrderAttachment.objects.all()
        queryset = Order.objects.filter(
            Q(status="En cours") | Q(status="Urgent")
        ).prefetch_related(
            Prefetch('attachments', queryset=attachments)
        ).order_by("-created_at")[:20]
        return queryset


class Dashboard(ListView):
    paginate_by = 20
    model = Order
    template_name = "webapp/dashboard.html"
    context_object_name = "orders"
    ordering = ["-id"]

    def get_context_data(self, **kwargs):
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


        return context
