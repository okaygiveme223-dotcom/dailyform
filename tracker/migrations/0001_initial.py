from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="AccountRecords",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("records", models.JSONField(default=list)),
                ("revision", models.PositiveBigIntegerField(default=0)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="AuthAttempt",
            fields=[
                ("key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("window", models.DateTimeField()),
                ("attempts", models.PositiveIntegerField(default=0)),
            ],
        ),
    ]
