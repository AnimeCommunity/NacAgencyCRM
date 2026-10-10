from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0004_configsmtp_singleton_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configsmtp",
            name="email_password",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Credencial SMTP cifrada; nunca se devuelve mediante la API.",
                max_length=512,
            ),
        ),
    ]
