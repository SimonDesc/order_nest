from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

# Importations des vues
from .views.orders import CreateOrder, EditOrder, DeleteOrder, SearchOrder, print_pdf
from .views.products import AddProductsToOrder, DeleteProduct, EditProduct, product_order_list
from .views.customers import autocomplete, get_customers, CreateCustomer
from .views.other_views import WebappHome, Dashboard, CustomerView, EditCustomer
from .views.api import DeleteOrderAttachment, get_canvas, get_orders, save_attachment, deactivate_customer
from .views.sms import modal_sms, modal_sms_customer, send_sms, get_credit_sms


app_name = 'webapp'

urlpatterns = [
    # Authentification
    path('login/', LoginView.as_view(template_name='webapp/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='webapp:login'), name='logout'),

    # Pages principales
    path('', WebappHome.as_view(), name='home'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),

    # Commandes
    path('orders/create/', CreateOrder.as_view(), name='order-create'),
    path('orders/<int:pk>/edit/', EditOrder.as_view(), name='order-edit'),
    path('orders/<int:pk>/delete/', DeleteOrder.as_view(), name='order-delete'),
    path('orders/search/', SearchOrder.as_view(), name='order-search'),
    path('orders/<int:pk>/add-products/', AddProductsToOrder.as_view(), name='order-add-products'),
    path('print_pdf/<int:pk>/', print_pdf, name='print_pdf'),

    # Produits
    path('products/<int:pk>/edit/', EditProduct.as_view(), name='product-edit'),
    path('products/<int:pk>/delete/', DeleteProduct.as_view(), name='product-delete'),  
    path('product_order_list/<int:order_id>/', product_order_list, name='product_order_list'),

    # Clients
    path('customers/', CustomerView.as_view(), name='customer'),
    path('customers/<int:pk>/edit/', EditCustomer.as_view(), name='customer-edit'),
    path('customers/create/', CreateCustomer.as_view(), name='customer-create'),
    path('autocomplete/', autocomplete, name='autocomplete'),
    path('get_customers/', get_customers, name='get_customers'),
    path('deactivate_customer/<int:pk>/', deactivate_customer, name='deactivate_customer'),

    # API et Pièces jointes
    path('save_canvas/', save_attachment, name='save_canvas'),
    path('save_pictures/', save_attachment, name='save_pictures'),
    path('delete_canvas/<int:pk>/', DeleteOrderAttachment.as_view(), name='delete_canvas'),
    path('delete_picture/<int:pk>/', DeleteOrderAttachment.as_view(), name='delete_picture'),
    path('get_canvas/<int:pk>/', get_canvas, name='get_canvas'),
    path('get_orders/', get_orders, name='get_orders'),

    # SMS
    path('modal_sms/<int:pk>/', modal_sms, name='modal_sms'),
    path('modal_sms_customer/<int:pk>/', modal_sms_customer, name='modal_sms_customer'),
    path('send_sms/', send_sms, name='send_sms'),
    path('get_credit_sms/', get_credit_sms, name='get_credit_sms'),
]

# Configuration pour le mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
