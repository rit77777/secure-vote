# Generated by Django 3.2.10 on 2022-06-13 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20220613_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registeredvoters',
            name='phone',
            field=models.CharField(max_length=10, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='uniqueid',
            name='phone',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]