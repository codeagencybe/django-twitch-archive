# Generated by Django 3.1 on 2020-08-12 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clips', '0007_auto_20200813_0146'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='box_art_url',
            field=models.URLField(default='0', max_length=150),
        ),
    ]