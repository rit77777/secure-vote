# Generated by Django 3.2.10 on 2022-03-27 05:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_registeredvoters_account_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='Constituency',
            fields=[
                ('c_id', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('c_name', models.CharField(max_length=100, null=True)),
            ],
        ),
    ]
