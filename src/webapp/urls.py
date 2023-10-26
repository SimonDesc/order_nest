from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import WebappLogin, WebappHome, CreateOrder, EditOrder, DeleteOrder, SearchOrder, Dashboard, DetailOrder, \
    DeleteProduct, EditProduct, AddProductsToOrder, get_clients, save_canvas, DeleteCanvas

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

    # Attachment Routes
    path('delete_canvas/<int:pk>', DeleteCanvas.as_view(), name='delete_canvas'),

    # API Routes
    path('get_clients/', get_clients, name='get_clients'),
    path('save_canvas/', save_canvas, name='save_canvas'),



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)