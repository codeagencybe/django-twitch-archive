# Generated by Django 3.1 on 2020-08-12 23:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clips', '0006_game'),
    ]

    operations = [
        migrations.RenameField(
            model_name='game',
            old_name='title',
            new_name='name',
        ),
    ]