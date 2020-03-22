import json
from django.shortcuts import render, redirect
from . import models

# Create your views here.
def home(request):
    supermarkets = models.Supermarket.objects.all().values('name', 'pk')
    context = {
        'supermarkets': supermarkets
    }
    return render(request, 'base.html', context=context)

def add_supermarket(request):
    name = request.POST.get('name')
    supermarkets = models.Supermarket.objects.all()
    if supermarkets.get(name=name):
        context = {
            'supermarkets': supermarkets,
            'error_message': 'Supermercado ja existente!',
        }
        return render(request, 'base.html', context=context)

    email = request.POST.get('email')
    models.Supermarket.objects.create(name=name, email=email)
    return redirect(home)

def add_products(request):
    supermarket_pk = request.POST.get('supermarket')
    supermarket = models.Supermarket.objects.get(pk=supermarket_pk)
    products = json.loads(request.POST.get('products'))
    for product in products:
        try:
            supermarket_product = supermarket.products.get(name=product["name"])
            supermarket_product.quantity += product["quantity"]
            supermarket_product.price = product["price"]
            supermarket_product.save()
        except models.Product.DoesNotExist:
            new_product = models.Product.objects.create(name=product["name"], price=product["price"], quantity=product["quantity"])
            supermarket.products.add(new_product)
    return redirect(home)
