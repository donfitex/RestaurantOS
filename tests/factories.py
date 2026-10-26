from decimal import Decimal

import factory
from django.contrib.auth import get_user_model

from apps.inventory.models import Ingredient, InventoryItem
from apps.menu.models import MenuCategory, MenuItem
from apps.restaurants.models import Branch, Restaurant
from apps.tables.models import Table


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"guest{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.django.Password("Test-password-835!")


class RestaurantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Restaurant

    name = factory.Sequence(lambda n: f"Restaurant {n}")


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    restaurant = factory.SubFactory(RestaurantFactory)
    name = factory.Sequence(lambda n: f"Branch {n}")
    tax_rate = Decimal("0.0750")


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MenuCategory

    restaurant = factory.SubFactory(RestaurantFactory)
    name = factory.Sequence(lambda n: f"Category {n}")


class MenuItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MenuItem

    branch = factory.SubFactory(BranchFactory)
    category = factory.SubFactory(
        CategoryFactory, restaurant=factory.SelfAttribute("..branch.restaurant")
    )
    name = "Rice bowl"
    sku = factory.Sequence(lambda n: f"item-{n}")
    price = Decimal("1000.00")


class TableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Table

    branch = factory.SubFactory(BranchFactory)
    table_number = factory.Sequence(lambda n: str(n))
    capacity = 4


class IngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ingredient

    restaurant = factory.SubFactory(RestaurantFactory)
    name = "Rice"
    sku = factory.Sequence(lambda n: f"ingredient-{n}")
    unit = "KG"
    minimum_stock = Decimal("1.000")


class InventoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InventoryItem

    branch = factory.SubFactory(BranchFactory)
    ingredient = factory.SubFactory(
        IngredientFactory, restaurant=factory.SelfAttribute("..branch.restaurant")
    )
    quantity = Decimal("5.000")
