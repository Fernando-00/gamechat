# Generated by Django 4.0.6 on 2022-07-30 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_alter_steamrecent_gameimg'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='steamadd',
            field=models.BooleanField(default=False),
        ),
    ]