from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_communitycommentlike'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitypost',
            name='images',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
