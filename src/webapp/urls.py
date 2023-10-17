from django.urls import path
from .views import WebappLogin, WebappHome, CreateOrder, EditOrder, DeleteOrder, Search, Dashboard, DetailOrder, Products, AddProduct, DeleteProduct, EditProduct

app_name = 'webapp'

urlpatterns = [
    path('', WebappLogin.as_view(), name='login'),
    path('home/', WebappHome.as_view(), name='home'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('create/', CreateOrder.as_view(), name='create'),
    path('order/<int:pk>/', DetailOrder.as_view(), name='order'),
    path('edit_order/<int:pk>/', EditOrder.as_view(), name='edit_order'),
    path('delete/<int:pk>/', DeleteOrder.as_view(), name='delete'),
    path('edit_product/<int:pk>/', EditProduct.as_view(), name='edit_product'),
    path('search/', Search.as_view(), name='search'),
    path('delete_product/<int:pk>/', DeleteProduct.as_view(), name='delete_product'),
    path('products/', Products.as_view(), name='products'),
    path('create_product/', AddProduct.as_view(), name='create_product'),


]
