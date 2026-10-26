"""Idempotent local demonstration data; never runs automatically in production."""

import os
from datetime import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.inventory.models import Ingredient, InventoryItem, Recipe, RecipeIngredient
from apps.inventory.services import adjust_stock
from apps.menu.models import MenuCategory, MenuItem
from apps.restaurants.models import Branch, OperatingHours, Restaurant
from apps.tables.models import Table


class Command(BaseCommand):
    help = "Create local demo accounts, menu, tables, recipes and audited opening stock."

    @transaction.atomic
    def handle(self, *args, **options):
        from django.conf import settings

        if not getattr(settings, "SERVE_LOCAL_MEDIA", False):
            raise CommandError("Demo data is permitted only in development/local settings.")
        password = os.getenv("DEMO_PASSWORD")
        if not password or len(password) < 16:
            raise CommandError("Set a local DEMO_PASSWORD with at least 16 characters.")
        users = {}
        for username, role in [
            ("admin", "ADMIN"),
            ("manager", "MANAGER"),
            ("waiter", "WAITER"),
            ("cashier", "CASHIER"),
            ("kitchen", "KITCHEN"),
            ("inventory", "INVENTORY_MANAGER"),
            ("customer", "CUSTOMER"),
        ]:
            user, created = get_user_model().objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@restaurantos.local",
                    "role": role,
                    "is_staff": role == "ADMIN",
                    "is_superuser": role == "ADMIN",
                },
            )
            if user.email != f"{username}@restaurantos.local":
                raise CommandError(
                    f"Existing account {username} is not a demo account; refusing to alter it."
                )
            if created:
                user.set_password(password)
                user.save()
            users[username] = user
        restaurant, _ = Restaurant.objects.get_or_create(
            name="RestaurantOS Demo Kitchen",
            defaults={
                "description": "Demonstration data. Replace with your restaurant configuration.",
                "currency": "NGN",
                "timezone": "Africa/Lagos",
            },
        )
        branch, _ = Branch.objects.get_or_create(
            restaurant=restaurant,
            name="Demo Lagos Kitchen",
            defaults={
                "address": "Demo location ? replace with your restaurant address",
                "tax_rate": Decimal("0.075"),
            },
        )
        branch.managers.add(users["manager"])
        branch.staff.add(*(user for user in users.values() if user.role != "CUSTOMER"))
        for weekday in range(7):
            OperatingHours.objects.get_or_create(
                branch=branch,
                weekday=weekday,
                defaults={"opens_at": time(8), "closes_at": time(22)},
            )
        for number, capacity in [("1", 2), ("2", 2), ("3", 4), ("4", 4), ("5", 6), ("6", 8)]:
            Table.objects.get_or_create(
                branch=branch,
                table_number=number,
                defaults={"capacity": capacity, "location": "Main dining room"},
            )
        ingredients = {}
        for sku, name, unit, minimum, quantity in [
            ("RICE", "Rice", "KG", "5", "20"),
            ("CHICKEN", "Chicken portions", "UNIT", "8", "30"),
            ("BUN", "Burger buns", "UNIT", "6", "24"),
            ("BEEF", "Beef patties", "UNIT", "6", "24"),
            ("GREENS", "Mixed greens", "KG", "2", "10"),
            ("CITRUS", "Citrus blend", "L", "3", "15"),
            ("CHOCOLATE", "Chocolate", "KG", "2", "10"),
        ]:
            ingredient, _ = Ingredient.objects.get_or_create(
                restaurant=restaurant,
                sku=sku,
                defaults={"name": name, "unit": unit, "minimum_stock": Decimal(minimum)},
            )
            stock, created = InventoryItem.objects.get_or_create(
                branch=branch, ingredient=ingredient
            )
            if created:
                adjust_stock(
                    inventory_item=stock,
                    quantity=quantity,
                    kind="PURCHASE",
                    actor=users["admin"],
                    notes="Demo opening stock",
                    reference=f"demo-opening-{sku}",
                )
            ingredients[sku] = ingredient
        catalog = [
            (
                "JOLLOF",
                "Smoky jollof bowl",
                "House favourites",
                "4500",
                "Slow-cooked rice with a rich tomato base and a fresh side salad.",
                [("RICE", ".300"), ("GREENS", ".100")],
            ),
            (
                "CHICKEN-PLATE",
                "Grilled chicken plate",
                "House favourites",
                "6500",
                "A generous grilled chicken portion with rice and greens.",
                [("CHICKEN", "1"), ("RICE", ".200"), ("GREENS", ".100")],
            ),
            (
                "BURGER",
                "Signature beef burger",
                "House favourites",
                "5800",
                "A juicy beef patty, crisp greens, and a soft toasted bun.",
                [("BUN", "1"), ("BEEF", "1"), ("GREENS", ".050")],
            ),
            (
                "SALAD",
                "Garden greens",
                "Fresh & light",
                "3500",
                "A bright, fresh bowl of seasonal greens.",
                [("GREENS", ".250")],
            ),
            (
                "COOLER",
                "Fresh citrus cooler",
                "Drinks",
                "2200",
                "A refreshing citrus blend, served chilled.",
                [("CITRUS", ".350")],
            ),
            (
                "BROWNIE",
                "Chocolate brownie",
                "Desserts",
                "2800",
                "A rich chocolate finish to your meal.",
                [("CHOCOLATE", ".100")],
            ),
        ]
        for sku, name, category_name, price, description, recipe_lines in catalog:
            category, _ = MenuCategory.objects.get_or_create(
                restaurant=restaurant, name=category_name
            )
            item, _ = MenuItem.objects.get_or_create(
                branch=branch,
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "price": Decimal(price),
                    "description": description,
                },
            )
            recipe, created = Recipe.objects.get_or_create(menu_item=item)
            if created:
                RecipeIngredient.objects.bulk_create(
                    [
                        RecipeIngredient(
                            recipe=recipe,
                            ingredient=ingredients[ingredient],
                            quantity=Decimal(quantity),
                        )
                        for ingredient, quantity in recipe_lines
                    ]
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Demo ready: 7 accounts, 6 dishes, 6 tables. Passwords are not printed. Existing stock and account passwords were preserved."
            )
        )
