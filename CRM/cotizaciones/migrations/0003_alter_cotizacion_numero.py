from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0002_rename_fecha_emision_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cotizacion",
            name="numero",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
