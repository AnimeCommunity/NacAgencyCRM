from django.db import migrations


def clear_legacy_plaintext_passwords(apps, schema_editor):
    ConfigSMTP = apps.get_model("marketing", "ConfigSMTP")
    ConfigSMTP.objects.exclude(email_password="").update(email_password="")


class Migration(migrations.Migration):
    dependencies = [
        ("marketing", "0005_alter_configsmtp_email_password"),
    ]

    operations = [
        migrations.RunPython(
            clear_legacy_plaintext_passwords,
            migrations.RunPython.noop,
        ),
    ]
