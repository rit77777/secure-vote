# Generated by Django 3.2.10 on 2022-03-28 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_constituency_is_active'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Candidate',
        ),
        migrations.AddField(
            model_name='constituency',
            name='node_address',
            field=models.URLField(null=True),
        ),
    ]