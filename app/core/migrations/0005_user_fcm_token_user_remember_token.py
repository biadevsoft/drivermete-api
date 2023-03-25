# Generated by Django 4.1.7 on 2023-03-24 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_rename_user_id_userdetail_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='fcm_token',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='fcm token'),
        ),
        migrations.AddField(
            model_name='user',
            name='remember_token',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='remember token'),
        ),
    ]