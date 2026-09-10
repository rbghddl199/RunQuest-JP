from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendationitem',
            name='location_score',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name='recommendationsession',
            name='current_latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='recommendationsession',
            name='current_longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='recommendationsession',
            name='location_priority_weight',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name='recommendationsession',
            name='returning_recent_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
