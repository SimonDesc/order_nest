from django.urls import path
from .views import WebappLogin, WebappHome, CreateOrder, EditOrder, DeleteOrder, SearchOrder, Dashboard, DetailOrder, \
    DeleteProduct, EditProduct, AddProductsToOrder, get_clients

app_name = 'webapp'

urlpatterns = [
    # Primary Routes
    path('', WebappLogin.as_view(), name='login'),
    path('home/', WebappHome.as_view(), name='home'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),

    # Order Routes
    path('orders/create/', CreateOrder.as_view(), name='order-create'),
    path('orders/<int:pk>/', DetailOrder.as_view(), name='order-detail'),
    path('orders/<int:pk>/edit/', EditOrder.as_view(), name='order-edit'),
    path('orders/<int:pk>/delete/', DeleteOrder.as_view(), name='order-delete'),
    path('orders/<int:pk>/add-products/', AddProductsToOrder.as_view(), name='order-add-products'),
    path('orders/search', SearchOrder.as_view(), name='order-search'),

    # Products Routes
    path('products/<int:pk>/edit/', EditProduct.as_view(), name='product-edit'),
    path('products/<int:pk>/delete/', DeleteProduct.as_view(), name='product-delete'),

    # API Routes
    path('get_clients/', get_clients, name='get_clients'),



]
