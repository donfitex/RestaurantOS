from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import ActiveModel, TimestampedModel


class Supplier(ActiveModel):
    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Ingredient(ActiveModel):
    class Unit(models.TextChoices):
        UNIT = "UNIT", "Unit"
        KG = "KG", "Kilogram"
        G = "G", "Gram"
        L = "L", "Litre"
        ML = "ML", "Millilitre"

    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=64)
    unit = models.CharField(max_length=4, choices=Unit.choices)
    minimum_stock = models.DecimalField(
        max_digits=14, decimal_places=3, default=0, validators=[MinValueValidator(0)]
    )
    maximum_stock = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    suppliers = models.ManyToManyField(Supplier, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "sku"], name="unique_restaurant_ingredient_sku"
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_stock__gte=0), name="ingredient_minimum_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(maximum_stock__isnull=True)
                | models.Q(maximum_stock__gte=models.F("minimum_stock")),
                name="ingredient_maximum_valid",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.unit})"


class InventoryItem(TimestampedModel):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="stock")
    branch = models.ForeignKey(
        "restaurants.Branch", on_delete=models.PROTECT, related_name="inventory"
    )
    quantity = models.DecimalField(
        max_digits=14, decimal_places=3, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "ingredient"], name="unique_branch_ingredient"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0), name="inventory_nonnegative"
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.branch_id
            and self.ingredient_id
            and self.branch.restaurant_id != self.ingredient.restaurant_id
        ):
            raise ValidationError("Ingredient and branch must belong to the same restaurant.")


class StockMovement(TimestampedModel):
    class Kind(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"
        WASTE = "WASTE", "Waste"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        RETURN = "RETURN", "Return"
        TRANSFER = "TRANSFER", "Transfer"

    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.PROTECT, related_name="movements"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    balance_after = models.DecimalField(max_digits=14, decimal_places=3)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~models.Q(quantity=0), name="movement_nonzero"),
            models.CheckConstraint(
                condition=models.Q(balance_after__gte=0), name="movement_balance_nonnegative"
            ),
        ]
        indexes = [models.Index(fields=["inventory_item", "created_at"])]


class Recipe(TimestampedModel):
    menu_item = models.OneToOneField(
        "menu.MenuItem", on_delete=models.PROTECT, related_name="recipe"
    )
    instructions = models.TextField(blank=True)


class RecipeIngredient(TimestampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="recipe_quantity_positive"
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.recipe_id
            and self.ingredient_id
            and self.recipe.menu_item.branch.restaurant_id != self.ingredient.restaurant_id
        ):
            raise ValidationError("Recipe ingredients must belong to the same restaurant.")


class StockAlert(TimestampedModel):
    inventory_item = models.OneToOneField(
        InventoryItem, on_delete=models.CASCADE, related_name="alert"
    )
    kind = models.CharField(max_length=20, default="LOW_STOCK", editable=False)
    is_active = models.BooleanField(default=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
