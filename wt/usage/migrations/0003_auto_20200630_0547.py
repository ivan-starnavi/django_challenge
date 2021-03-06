# Generated by Django 2.2.1 on 2020-06-30 05:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usage', '0002_aggregateddatausagerecord_aggregatedvoiceusagerecord'),
    ]

    operations = [
        migrations.RenameField(
            model_name='datausagerecord',
            old_name='att_subscription_id',
            new_name='att_subscription',
        ),
        migrations.RenameField(
            model_name='datausagerecord',
            old_name='sprint_subscription_id',
            new_name='sprint_subscription',
        ),
        migrations.RenameField(
            model_name='voiceusagerecord',
            old_name='att_subscription_id',
            new_name='att_subscription',
        ),
        migrations.RenameField(
            model_name='voiceusagerecord',
            old_name='sprint_subscription_id',
            new_name='sprint_subscription',
        ),
    ]
