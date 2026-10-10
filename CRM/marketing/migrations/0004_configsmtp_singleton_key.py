from django.db import migrations, models


def keep_single_smtp_configuration(apps, schema_editor):
    ConfigSMTP = apps.get_model("marketing", "ConfigSMTP")
    first = ConfigSMTP.objects.order_by("pk").first()
    if first is not None:
        ConfigSMTP.objects.exclude(pk=first.pk).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0003_alter_configsmtp_email_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="configsmtp",
            name="singleton_key",
            field=models.PositiveSmallIntegerField(default=1, editable=False),
        ),
        migrations.RunPython(
            keep_single_smtp_configuration,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="configsmtp",
            name="singleton_key",
            field=models.PositiveSmallIntegerField(default=1, editable=False, unique=True),
        ),
        migrations.AddConstraint(
            model_name="configsmtp",
            constraint=models.CheckConstraint(
                condition=models.Q(("singleton_key", 1)),
                name="marketing_configsmtp_singleton_key_is_one",
            ),
        ),
    ]
