# Generated by Django 4.0.2 on 2022-06-06 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_repository_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='readme_html',
            field=models.TextField(null=True),
        ),
    ]