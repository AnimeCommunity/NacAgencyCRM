from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("interacciones", "0003_rename_fecha_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="interaccion",
            name="resultado",
            field=models.CharField(
                choices=[
                    ("sin_definir", "Sin definir"),
                    ("contactado", "Contactado"),
                    ("sin_respuesta", "Sin respuesta"),
                    ("interesado", "Interesado"),
                    ("no_interesado", "No interesado"),
                    ("reunion_agendada", "Reunión agendada"),
                    ("cerrado", "Cierre concretado"),
                ],
                default="sin_definir",
                max_length=30,
            ),
        ),
    ]
