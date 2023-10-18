from django.db.models import Q, Prefetch
from django.http import JsonResponse
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
            customer_id = request.POST.get('id', None)  # Récupérer l'ID du champ caché

            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)  # Vérifier si le client existe déjà
                except Customer.DoesNotExist:
                    customer = None

            if not customer:
                customer = customer_form.save()  # Créer un nouveau client si nécessaire

            order = order_form.save(commit=False)
            order.customer = customer  # Utiliser le client existant ou le nouveau client
            order.save()

            return redirect('/dashboard')
        else:
            customer_id = request.POST.get('id', None)
            context = {
                'order_form': order_form,
                'customer_form': customer_form,
                'customer_id': customer_id,
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


class SearchOrder(ListView):
    model = Order
    template_name = 'webapp/orders/order-search.html'

    def get_queryset(self):
        query = self.request.GET.get("q")
        order_list = Order.objects.prefetch_related(
            Prefetch('customer', queryset=Customer.objects.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(address__icontains=query) |
                Q(mail__icontains=query) |
                Q(comments__icontains=query)
            ))
        ).filter(
            Q(label__icontains=query) |
            Q(comments__icontains=query) |
            Q(customer__first_name__icontains=query) |
            Q(customer__last_name__icontains=query) |
            Q(customer__phone_number__icontains=query) |
            Q(customer__address__icontains=query) |
            Q(customer__mail__icontains=query) |
            Q(customer__comments__icontains=query)
        )[:50]

        return order_list

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


def get_clients(request):
    query = request.GET.get('term', '')
    clients = Customer.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).values('id', 'first_name', 'last_name',
             'phone_number', 'address', 'mail',
             'comments'
             )[:10]

    results = []
    for client in clients:
        client_dict = {
            'id': client['id'],
            'first_name': client['first_name'],
            'last_name': client['last_name'],
            'phone_number': str(client['phone_number']),
            'address': client['address'],
            'mail': client['mail'],
            'comments': client['mail'],
            'label': f"{client['first_name']} {client['last_name']}",
        }
        results.append(client_dict)
        print(results)
    return JsonResponse(results, safe=False)

