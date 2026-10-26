from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db import migrations
from django.db.models.functions import Upper

INDEXES = [("menu_name_trigram", "name"), ("menu_description_trgm", "description"), ("menu_sku_trigram", "sku")]


def create_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    quote = schema_editor.quote_name
    for name, field in INDEXES:
        schema_editor.execute(f"CREATE INDEX {quote(name)} ON {quote('menu_menuitem')} USING gin (UPPER({quote(field)}) gin_trgm_ops)")


def remove_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for name, _ in INDEXES:
        schema_editor.execute(f"DROP INDEX {schema_editor.quote_name(name)}")


class Migration(migrations.Migration):
    dependencies = [("menu", "0003_alter_menuitem_image")]
    operations = [
        migrations.RemoveIndex(model_name="menuitem", name="menu_name_trigram"),
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunPython(create_indexes, remove_indexes)],
            state_operations=[migrations.AddIndex(model_name="menuitem", index=GinIndex(OpClass(Upper(field), name="gin_trgm_ops"), name=name)) for name, field in INDEXES],
        ),
    ]
