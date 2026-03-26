# Generated migration for adding reset_policy field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document_tracking', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documenttype',
            name='reset_policy',
            field=models.CharField(
                choices=[
                    ('none', 'Never reset (continuous sequence)'),
                    ('monthly', 'Reset monthly'),
                    ('yearly', 'Reset yearly')
                ],
                default='yearly',
                help_text='When to reset the sequence counter',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='trackingnumbersequence',
            name='month',
            field=models.IntegerField(
                null=True,
                blank=True,
                help_text='Month for monthly sequences (1-12)'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='trackingnumbersequence',
            unique_together={('document_type', 'year', 'month')},
        ),
    ]
