# Generated by Django 4.2 on 2023-04-11 23:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_manager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='manager',
        ),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('admin', 'Admin'), ('staff', 'Staff'), ('rider', 'Rider'), ('driver', 'Driver')], max_length=10, verbose_name='user type'),
        ),
    ]
