# Generated by Django 4.2.3 on 2023-07-07 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dca', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historylastupdated',
            name='id',
        ),
        migrations.AlterField(
            model_name='historylastupdated',
            name='ticker',
            field=models.CharField(max_length=12, primary_key=True, serialize=False),
        ),
    ]
