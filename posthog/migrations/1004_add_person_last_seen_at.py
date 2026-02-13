from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posthog', '1003_clean_up_stale_alert_subscriptions'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE posthog_person ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITH TIME ZONE NULL;',
            reverse_sql='ALTER TABLE posthog_person DROP COLUMN IF EXISTS last_seen_at;',
            state_operations=[
                migrations.AddField(
                    model_name='person',
                    name='last_seen_at',
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ]
        ),
    ]
