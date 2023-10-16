from django.urls import path
from .views import WebappLogin, WebappHome, CreateOrder, EditOrder, DeleteOrder, Search, Dashboard

app_name = 'webapp'

urlpatterns = [
    path('', WebappLogin.as_view(), name='login'),
    path('home/', WebappHome.as_view(), name='home'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('create/', CreateOrder.as_view(), name='create'),
    path('edit/', EditOrder.as_view(), name='edit'),
    path('delete/<int:pk>/', DeleteOrder.as_view(), name='delete'),
    path('search/', Search.as_view(), name='search'),

]
