from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import WebappHome, CreateOrder, EditOrder, DeleteOrder, SearchOrder, Dashboard, \
    DeleteProduct, EditProduct, AddProductsToOrder, get_clients, save_canvas, DeleteCanvas, get_canvas, get_orders

app_name = 'webapp'

urlpatterns = [
    # Identification Routes
    path('', LoginView.as_view(template_name='webapp/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='webapp:login'), name='logout'),


    # Primary Routes
    path('home/', WebappHome.as_view(), name='home'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),

    # Order Routes
    path('orders/create/', CreateOrder.as_view(), name='order-create'),
    path('orders/<int:pk>/edit/', EditOrder.as_view(), name='order-edit'),
    path('orders/<int:pk>/delete/', DeleteOrder.as_view(), name='order-delete'),
    path('orders/<int:pk>/add-products/', AddProductsToOrder.as_view(), name='order-add-products'),
    path('orders/search', SearchOrder.as_view(), name='order-search'),

    # Products Routes
    path('products/<int:pk>/edit/', EditProduct.as_view(), name='product-edit'),
    path('products/<int:pk>/delete/', DeleteProduct.as_view(), name='product-delete'),

    # Attachment Routes
    path('delete_canvas/<int:pk>', DeleteCanvas.as_view(), name='delete_canvas'),

    # API Routes
    path('get_clients/', get_clients, name='get_clients'),
    path('save_canvas/', save_canvas, name='save_canvas'),
    path('get_canvas/<int:pk>', get_canvas, name='get_canvas'),
    path('get_orders/', get_orders, name='get_orders'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
