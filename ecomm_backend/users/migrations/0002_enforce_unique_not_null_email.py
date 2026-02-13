from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "auth_user_email_uniq_idx ON auth_user(email);"
            ),
            reverse_sql="DROP INDEX IF EXISTS auth_user_email_uniq_idx;",
        ),
    ]

