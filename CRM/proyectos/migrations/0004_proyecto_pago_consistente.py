from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proyectos", "0003_proyecto_pago"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="proyecto",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(pagado=True, fecha_pago__isnull=False)
                    | models.Q(pagado=False, fecha_pago__isnull=True)
                ),
                name="proyecto_pago_fecha_consistente",
            ),
        ),
    ]