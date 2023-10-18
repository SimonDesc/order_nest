from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Customer, Order, OrderHasProduct, Status, Product
from .forms import NewOrderForm, NewCustomerForm, AddProductForm


class WebappLogin(TemplateView):
    template_name = 'webapp/login.html'


class WebappHome(ListView):
    model = Order
    template_name = 'webapp/home.html'
    context_object_name = "commandes"


class CreateOrder(CreateView):
    form_class = NewOrderForm
    template_name = 'webapp/orders/order-create.html'
    success_url = '/dashboard'

    def get_context_data(self, **kwargs):
        context = {
            'order_form': NewOrderForm(),
            'customer_form': NewCustomerForm(),
        }
        return context

    def post(self, request, *args, **kwargs):

        order_form = NewOrderForm(request.POST)
        customer_form = NewCustomerForm(request.POST)

        if order_form.is_valid() and customer_form.is_valid():
            customer = customer_form.save()
            order = order_form.save(commit=False)
            order.customer = customer
            order.save()

            return redirect('/dashboard')
        else:
            context = {
                'order_form': order_form,
                'customer_form': customer_form,
            }
            return render(request, self.template_name, context)


class EditOrder(UpdateView):
    model = Order
    form_class = NewOrderForm
    template_name = 'webapp/orders/order-edit.html'
    success_url = reverse_lazy('webapp:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['order_form'] = NewOrderForm(instance=order)
        customer_instance = order.customer
        context['customer_form'] = NewCustomerForm(instance=customer_instance)
        return context

    # Check la validité de form (order)
    def form_valid(self, form):
        customer_form = NewCustomerForm(self.request.POST, instance=self.object.customer)

        # Check la validité de customer
        if customer_form.is_valid():
            form.save()
            customer_form.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        customer_form = NewCustomerForm(self.request.POST, instance=self.object.customer)
        context = self.get_context_data()
        context['customer_form'] = customer_form
        return self.render_to_response(context)


class DeleteOrder(DeleteView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/orders/order-delete.html'
    success_url = reverse_lazy("webapp:dashboard")


class Search(TemplateView):
    template_name = 'webapp/search.html'


class DetailOrder(DetailView):
    model = Order
    context_object_name = "commandes"
    template_name = 'webapp/orders/order-detail.html'


class Dashboard(ListView):
    model = Order
    template_name = 'webapp/dashboard.html'
    context_object_name = "commandes"


class DeleteProduct(DeleteView):
    model = Product
    context_object_name = 'product'
    template_name = 'webapp/products/product-delete.html'
    success_url = reverse_lazy("webapp:product-list")

    
class EditProduct(UpdateView):
    model = Product
    fields = "__all__"
    template_name = 'webapp/products/product-edit.html'
    success_url = reverse_lazy("webapp:product-list")


class AddProductsToOrder(CreateView):
    model = Product
    fields = '__all__'
    template_name = 'webapp/orders/order-product.html'
    success_url = '/dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs['pk']
        all_product_filtered = OrderHasProduct.objects.all().filter(order_id=order_id)
        order_infos = Order.objects.get(pk=order_id)
        context['product_list'] = all_product_filtered
        context['order_id'] = order_id
        context['order_infos'] = order_infos
        return context

    def form_valid(self, form):
        order_id = self.kwargs['pk']
        order_object = Order.objects.get(pk=order_id)
        order_product = form.save()
        OrderHasProduct.objects.create(order=order_object, product=order_product)
        return super().form_valid(form)
