# Generated by Django 5.1.6 on 2025-02-22 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_jobdescription_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdescription',
            name='description_text',
            field=models.TextField(),
        ),
    ]
