from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('add-products/', views.add_products, name='add_products'),
    path('add-supermarket/', views.add_supermarket, name='add_supermarket'),
]