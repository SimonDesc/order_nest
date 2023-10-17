from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Customer, Order, OrderHasProduct, Status, Product
from .forms import NewOrderForm, NewCustomerForm, AddProductForm, AddProductOrderForm


class WebappLogin(TemplateView):
    template_name = 'webapp/login.html'


class WebappHome(ListView):
    model = Order
    template_name = 'webapp/home.html'
    context_object_name = "commandes"


class CreateOrder(CreateView):
    form_class = NewOrderForm
    template_name = 'webapp/create.html'
    success_url = '/dashboard'

    def get_context_data(self, **kwargs):
        context = {
            'order_form': NewOrderForm(),
            'customer_form': NewCustomerForm(),
        }
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        order_form = NewOrderForm(request.POST)
        customer_form = NewCustomerForm(request.POST)

        if order_form.is_valid() and customer_form.is_valid():
            customer = customer_form.save()  # Sauvegarder le client d'abord
            order = order_form.save(commit=False)  # Ne pas encore sauvegarder la commande
            order.customer = customer  # Établir la relation
            order.save()  # Maintenant, sauvegarder la commande
            return redirect('/dashboard')

        return render(request, self.template_name, self.get_context_data())


class EditOrder(UpdateView):
    model = Order

    form_class = NewOrderForm
    template_name = 'webapp/edit_order.html'
    success_url = reverse_lazy('webapp:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()

        context['order_form'] = NewOrderForm(instance=order)
        customer_instance = order.customer
        context['customer_form'] = NewCustomerForm(instance=customer_instance)

        return context

    def form_valid(self, form):
        customer_form = NewCustomerForm(self.request.POST, instance=self.object.customer)

        if customer_form.is_valid():
            self.object = form.save()
            customer_form.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)



class DeleteOrder(DeleteView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/delete.html'
    success_url = reverse_lazy("webapp:dashboard")


class Search(TemplateView):
    template_name = 'webapp/search.html'


class DetailOrder(DetailView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/order.html'


class Dashboard(ListView):
    model = Order
    template_name = 'webapp/dashboard.html'
    context_object_name = "commandes"


class Products(ListView):
    model = Product
    template_name = 'webapp/products.html'
    context_object_name = "products"


class AddProduct(CreateView):
    form_class = AddProductForm
    template_name = 'webapp/new_product.html'
    success_url = reverse_lazy("webapp:products")


class DeleteProduct(DeleteView):
    model = Product
    context_object_name = 'product'
    template_name = 'webapp/delete_product.html'
    success_url = reverse_lazy("webapp:products")

    
class EditProduct(UpdateView):
    model = Product
    fields = "__all__"
    template_name = 'webapp/edit_product.html'
    success_url = reverse_lazy("webapp:products")

