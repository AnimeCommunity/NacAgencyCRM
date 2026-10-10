from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cotizacion",
            old_name="fecha_emision",
            new_name="created_at",
        ),
    ]
