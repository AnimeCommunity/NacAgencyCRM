from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0003_cliente_origen"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cliente",
            old_name="fecha_registro",
            new_name="created_at",
        ),
    ]
