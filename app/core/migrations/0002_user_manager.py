# Generated by Django 4.2 on 2023-04-11 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='manager',
            field=models.BooleanField(default=False, verbose_name='manager'),
        ),
    ]
