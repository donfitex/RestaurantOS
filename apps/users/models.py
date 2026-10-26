from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"
        WAITER = "WAITER", "Waiter"
        KITCHEN = "KITCHEN", "Kitchen"
        INVENTORY_MANAGER = "INVENTORY_MANAGER", "Inventory manager"
        CUSTOMER = "CUSTOMER", "Customer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=32, blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.username
