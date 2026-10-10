from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proyectos", "0002_rename_descripción_proyecto_descripcion_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="fecha_pago",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="proyecto",
            name="pagado",
            field=models.BooleanField(default=False),
        ),
    ]
