# Imports Django
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import CreateView, UpdateView, DeleteView

# Imports relatifs à l'application
from ..forms import AddProductForm, AddProductsToOrder
from ..models import Order, OrderHasProduct, Product


def product_order_list(request, order_id):
    """
    This Python function calculates the total order amount, deposit, and remaining balance for a given
    order and renders the information in a template.
    
    :param request: The `request` parameter in the `product_order_list` function is typically an
    HttpRequest object that represents the current request from the user's browser. It contains
    information about the request, such as the user's session, GET and POST data, and more. This
    parameter is commonly used in Django views to
    :param order_id: The `order_id` parameter in the `product_order_list` function is used to identify a
    specific order for which the product list needs to be displayed. It is passed as an argument to the
    function to retrieve the order details and associated products for that order from the database
    :return: The `product_order_list` function is returning a rendered HTML template named
    "product_order_list.html" along with a context dictionary.
    """
    order = Order.objects.get(pk=order_id)
    product_order = OrderHasProduct.objects.filter(order=order_id)

    # Calculer le total pour chaque produit
    for product in product_order:
        product.total = product.product.selling_price_unit * 1
    total_order = sum(product.total for product in product_order)
    deposit = (total_order * 30 / 100)
    remaining = (total_order - order.deposit)
    
    context = {
        "remaining" : remaining,
        "order": order,
        "product_order": product_order,
        "order_id": order_id,
        "total_order": total_order,
        "deposit" : deposit,
    }
    return render(request, "webapp/products/product_order_list.html", context)


class DeleteProduct(DeleteView):
    """
    This class is a Django DeleteView subclass for deleting a Product object with custom success URL and
    form validation.
    """
    model = Product
    context_object_name = "product"
    template_name = "webapp/products/product-delete.html"

    def get_success_url(self):
        return ""

    def form_valid(self, form):
        response = super().form_valid(form)
        return HttpResponse(status=204, headers={"HX-Trigger": "ProductsListChanged"})


class EditProduct(UpdateView):
    """
    The `EditProduct` class is a view in a Django application that allows users to edit product
    information and save changes to the database.
    """
    model = Product
    form_class = AddProductsToOrder
    template_name = "webapp/products/product-edit.html"
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        request.session["previous_url"] = request.META.get("HTTP_REFERER", "/")
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.get("previous_url", "/")

    def form_valid(self, form):
        form.save()
        return HttpResponse(status=204, headers={"HX-Trigger": "ProductsListChanged"})

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class AddProductsToOrder(CreateView):
    """
    The `AddProductsToOrder` class in Python is a view that handles adding products to an order, storing
    previous URL in session, displaying product and order information, and processing form submissions.
    """
    form_class = AddProductForm

    template_name = "webapp/orders/order-product.html"

    def get(self, request, *args, **kwargs):
        request.session["previous_url"] = request.META.get("HTTP_REFERER", "/")
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.get("previous_url", "/")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs["pk"]
        all_product_filtered = OrderHasProduct.objects.all().filter(order_id=order_id)
        order_infos = Order.objects.get(pk=order_id)
        context["product_list"] = all_product_filtered
        context["order_id"] = order_id
        context["order_infos"] = order_infos
        return context

    def form_valid(self, form):
        order_id = self.kwargs["pk"]
        order_object = Order.objects.get(pk=order_id)
        
        order_product = form.save(commit=False)

        order_product = form.save()
        
        OrderHasProduct.objects.create(order=order_object, product=order_product)
        return HttpResponse(status=204, headers={"HX-Trigger": "ProductsListChanged"})

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
