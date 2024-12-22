from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_level = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer_name = models.CharField(max_length=200)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=50, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order for {self.customer_name} - {self.product.name}"
