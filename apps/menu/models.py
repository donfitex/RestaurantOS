from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import ActiveModel, TimestampedModel


class MenuCategory(ActiveModel):
    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.PROTECT, related_name="categories")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["restaurant", "name"], name="unique_restaurant_category")]

    def __str__(self):
        return self.name


class MenuItem(ActiveModel):
    branch = models.ForeignKey("restaurants.Branch", on_delete=models.PROTECT, related_name="menu_items")
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to="menu/%Y/%m/", blank=True)
    sku = models.CharField(max_length=64)
    availability = models.BooleanField(default=True, db_index=True)
    preparation_time = models.PositiveSmallIntegerField(default=15)
    modifiers = models.ManyToManyField("MenuModifier", through="MenuItemModifier", related_name="menu_items")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["branch", "sku"], name="unique_branch_menu_sku"), models.CheckConstraint(condition=models.Q(price__gte=0), name="menu_price_nonnegative")]
        indexes = [models.Index(fields=["branch", "availability", "category"])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.branch_id and self.category_id and self.branch.restaurant_id != self.category.restaurant_id:
            raise ValidationError({"category": "Category must belong to the branch restaurant."})

    def __str__(self):
        return self.name


class MenuModifier(ActiveModel):
    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=0), name="modifier_price_nonnegative")]

    def __str__(self):
        return self.name


class MenuItemModifier(TimestampedModel):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    modifier = models.ForeignKey(MenuModifier, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["menu_item", "modifier"], name="unique_item_modifier")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.menu_item_id and self.modifier_id and self.menu_item.branch.restaurant_id != self.modifier.restaurant_id:
            raise ValidationError("Modifier must belong to the same restaurant.")
