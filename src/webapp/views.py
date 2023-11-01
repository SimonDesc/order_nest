import base64
import datetime
import json
import os.path

from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.files.base import ContentFile

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from .models import Customer, Order, OrderHasProduct, Product, OrderAttachment
from .forms import NewOrderForm, NewCustomerForm, AddProductsToOrder


class WebappHome(ListView):
    model = Order
    template_name = 'webapp/home.html'
    context_object_name = "commandes"

    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')[:20]


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
            customer_id = request.POST.get('id', None)

            # On récupère le client (existant ou nouveau)
            customer, is_existing_customer = self.get_or_create_customer(customer_id, customer_form)
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
            return redirect('/dashboard')
        else:
            # Si le formulaire n'est pas valide
            # On renvoi le context + l'id du client
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
        context['product_order'] = OrderHasProduct.objects.filter(order=order.id)
        context['attachments'] = OrderAttachment.objects.filter(order=order.id)
        return context

    # Check la validité de form (order)
    def form_valid(self, form):
        # Check la validité de customer
        customer_form = NewCustomerForm(self.request.POST, instance=self.object.customer)
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
    template_name = "webapp/orders/order-search.html"

    def get_queryset(self):
        query = self.request.GET.get("q")
        order_list = (
            Order.objects.filter(
                        Q(label__icontains=query) # libellé
                        |
                        Q(status__label__icontains=query) # status
                        |
                        Q(pk__icontains=query) # id
                        |
                        Q(customer__first_name__icontains=query)
                        |
                        Q(customer__last_name__icontains=query)
                        |
                        Q(customer__mail__icontains=query)
                        |
                        Q(customer__address__icontains=query)
                        |
                        Q(customer__phone_number__icontains=query)
                )[:50]
        )
        return order_list


class Dashboard(ListView):
    paginate_by = 20
    model = Order
    template_name = 'webapp/dashboard.html'
    context_object_name = "orders"
    ordering = ['-id']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_number = context['page_obj'].number
        element_by_page = self.paginate_by
        all_objects = Order.objects.all()

        count_all = Paginator(all_objects, element_by_page)
        context['total_obj'] = count_all.count

        accumulated_objects = (page_number - 1) * element_by_page + len(context['page_obj'])
        context['accumulated_objects'] = accumulated_objects

        return context


class DeleteProduct(DeleteView):
    model = Product
    context_object_name = 'product'
    template_name = 'webapp/products/product-delete.html'

    def get(self, request, *args, **kwargs):
        request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.get('previous_url', '/')


class EditProduct(UpdateView):
    model = Product
    form_class = AddProductsToOrder
    template_name = 'webapp/products/product-edit.html'
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.get('previous_url', '/')


class AddProductsToOrder(CreateView):
    model = Product
    fields = '__all__'
    template_name = 'webapp/orders/order-product.html'

    def get(self, request, *args, **kwargs):
        request.session['previous_url'] = request.META.get('HTTP_REFERER', '/')
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.get('previous_url', '/')

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


def get_canvas(request, pk):
    order = OrderAttachment.objects.filter(order_id=pk)

    for e in order.all():
        file_json = e.canvas_json

    if order:
        return JsonResponse(
            {'exit': True,
             'json_file': file_json
             })
    return HttpResponse(False)


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

    return JsonResponse(results, safe=False)


def save_canvas(request):
    if request.method == "POST":
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        data = json.loads(request.body.decode("utf-8"))
        data_url = data.get('img')
        order_id = data.get('order_id')
        drawing_data = data.get('drawingData')

        # Decode image
        format, imgstr = data_url.split(';base64,')
        ext = format.split('/')[-1]

        file_name = f"image_{current_time}.{ext}"
        data = ContentFile(base64.b64decode(imgstr), name=file_name)

        # On créer l'objet OrderAttachment
        attachment = OrderAttachment()

        # On récupère l'id de la cde
        order = Order.objects.get(pk=order_id)

        # Ajout de l'image
        attachment.order = order
        attachment.file = data
        attachment.canvas_json = drawing_data
        attachment.save()

        return HttpResponse(str(file_name))


def get_orders(request):
    orders = Order.objects.all().order_by('-created_at')

    order_list = []
    for order in orders:
        order_dict = {
            'IDorder': str(order.pk),
            'customer': str(order.customer.last_name + ' ' + order.customer.first_name)[0:20] + "..." if len(str(order.customer.last_name + ' ' + order.customer.first_name)) > 19 else str(order.customer.last_name + ' ' + order.customer.first_name)[0:20],
            'label': str(order.label)[0:20] + "..." if len(str(order.label)) > 14 else str(order.label)[0:20],
            'status': str(order.status),
            'created': order.created_at.strftime('%d/%m/%Y'),
            'url': str(reverse('webapp:order-edit', kwargs={'pk': order.pk}))
        }
        order_list.append(order_dict)

    data = {'results': order_list}
    return JsonResponse(data)


class DeleteCanvas(DeleteView):
    model = OrderAttachment

    def get_success_url(self):
        order_id = self.object.pk
        return reverse('webapp:order-edit', args=[order_id])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.file:
            file_path = os.path.join(settings.MEDIA_ROOT, self.object.file.path)
            if os.path.exists(file_path):
                os.remove(file_path)
        self.object.delete()
        return JsonResponse({'status': 'success'})


