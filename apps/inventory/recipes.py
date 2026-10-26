from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError
from apps.menu.models import MenuItem
from .models import Recipe, RecipeIngredient, Ingredient


@transaction.atomic
def replace_recipe(*, menu_item, ingredients, instructions=""):
    menu_item = MenuItem.objects.select_for_update().select_related("branch").get(pk=menu_item.pk)
    if not ingredients:
        raise ValidationError("A recipe needs at least one ingredient.")
    recipe, _ = Recipe.objects.get_or_create(menu_item=menu_item)
    seen = set()
    rows = []
    for line in ingredients:
        ingredient = Ingredient.objects.get(pk=line["ingredient"])
        quantity = Decimal(str(line["quantity"]))
        if not quantity.is_finite() or quantity <= 0 or quantity != quantity.quantize(Decimal("0.001")):
            raise ValidationError("Recipe quantities must be positive with at most three decimal places.")
        if ingredient.pk in seen or ingredient.restaurant_id != menu_item.branch.restaurant_id or not ingredient.is_active:
            raise ValidationError("Duplicate, inactive, or cross-restaurant ingredient.")
        seen.add(ingredient.pk)
        rows.append(RecipeIngredient(recipe=recipe, ingredient=ingredient, quantity=quantity))
    recipe.ingredients.all().delete()
    RecipeIngredient.objects.bulk_create(rows)
    recipe.instructions = instructions
    recipe.save(update_fields=["instructions", "updated_at"])
    return recipe
