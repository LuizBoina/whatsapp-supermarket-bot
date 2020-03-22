from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext as _

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=300)
    price = models.DecimalField(_(u'Price'), max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0.05, message="Preco minimo eh 5 centavos")])
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['name']

class Supermarket(models.Model):
    name = models.CharField(_("Name"), max_length=300, unique=True) #virgula nao
    products = models.ManyToManyField(Product, _("Products"), blank=True)
    email = models.EmailField(_("Email"), max_length=254)
    #password
    #def __str__(self):
    #    return '({},{})'.format(self.pk, self.name)
