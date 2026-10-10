from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("interacciones", "0002_interaccion_created_by_alter_interaccion_tipo"),
    ]

    operations = [
        migrations.RenameField(
            model_name="interaccion",
            old_name="fecha",
            new_name="created_at",
        ),
    ]
