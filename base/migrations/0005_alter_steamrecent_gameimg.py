# Generated by Django 4.0.6 on 2022-07-29 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_steamrecent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='steamrecent',
            name='gameImg',
            field=models.ImageField(null=True, upload_to=''),
        ),
    ]
