import os
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings

from apps.inventory.models import StockMovement
from apps.menu.models import MenuItem

pytestmark = pytest.mark.django_db


@override_settings(SERVE_LOCAL_MEDIA=True)
@patch.dict(os.environ, {"DEMO_PASSWORD": "Local-demo-password-835!"})
def test_demo_seed_is_repeatable_without_resetting_stock_or_passwords():
    call_command("seed_demo")
    user = get_user_model().objects.get(username="admin")
    original_password = user.password
    movement_count = StockMovement.objects.count()
    call_command("seed_demo")
    user.refresh_from_db()
    assert user.password == original_password
    assert MenuItem.objects.count() == 6
    assert StockMovement.objects.count() == movement_count == 7
