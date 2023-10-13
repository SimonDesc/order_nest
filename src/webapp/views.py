from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Customer, Order, OrderHasProduct, Status, Product


class WebappLogin(TemplateView):
    template_name = 'webapp/login.html'


class WebappHome(ListView):
    model = Order
    template_name = 'webapp/home.html'
    context_object_name = "commandes"

    @property
    def total_price(self):
        total = 0
        for relation in self.orderhasproduct_set.all():
            total += relation.product.selling_price_unit
            return total

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

class CreateOrder(TemplateView):
    template_name = 'webapp/create.html'


class EditOrder(TemplateView):
    template_name = 'webapp/edit.html'


class DeleteOrder(TemplateView):
    template_name = 'webapp/delete.html'


class Search(TemplateView):
    template_name = 'webapp/search.html'


class Dashboard(TemplateView):
    template_name = 'webapp/dashboard.html'
