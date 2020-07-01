from datetime import timedelta
from typing import Type

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from wt.att_subscriptions.models import ATTSubscription
from wt.plans.models import Plan
from wt.sprint_subscriptions.models import SprintSubscription
from wt.usage.base_models import UsageRecord
from wt.usage.models import DataUsageRecord, VoiceUsageRecord


class BaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(username='user', password='123')
        cls.plan = Plan.objects.create(name='test', price='1.00', data_available=100)

        cls.today = timezone.now()
        cls.today_date = cls.today.date()
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.tomorrow_date = cls.tomorrow.date()

    def create_att(self):
        return ATTSubscription.objects.create(
            user=self.user, plan=self.plan, status='new', device_id='test', phone_number='test', phone_model='test',
            network_type='test', effective_date=timezone.now(), deleted=False
        )

    def create_sprint(self):
        return SprintSubscription.objects.create(
            user=self.user, plan=self.plan, status='new', device_id='test', phone_number='test', phone_model='test',
            sprint_id='test', effective_date=timezone.now(), deleted=False
        )

    @staticmethod
    def _create_usage(model: Type[UsageRecord], subscription: UsageRecord, price, usage, usage_date):
        usage_date = usage_date if usage_date is not None else timezone.now()

        if isinstance(subscription, ATTSubscription):
            field_name = 'att_subscription'
        elif isinstance(subscription, SprintSubscription):
            field_name = 'sprint_subscription'
        else:
            raise RuntimeError('Unknown subscription object: it should be ATTSubscription or SprintSubscription')

        return model.objects.create(
            **{
                field_name: subscription,
                model.USAGE_FIELD: usage
            },
            price=price,
            usage_date=usage_date
        )

    def create_data_usage(self, subscription, price, kilobytes, usage_date=None):
        return self._create_usage(DataUsageRecord, subscription, price, kilobytes, usage_date)

    def create_voice_usage(self, subscription, price, seconds, usage_date=None):
        return self._create_usage(VoiceUsageRecord, subscription, price, seconds, usage_date)

    def create_basic_test_set(self):
        # create subscriptions
        sub_att = self.create_att()
        sub_sprint = self.create_sprint()

        # create usages
        #   att
        for usage, date in zip([1, 10, 100], [self.today, self.tomorrow, self.today]):
            self.create_data_usage(sub_att, 1, usage, date)
        self.create_voice_usage(sub_att, 1, 5, self.today)
        #   sprint
        self.create_data_usage(sub_sprint, 1, 5, self.tomorrow)
        for usage, date in zip([2, 20, 200], [self.tomorrow, self.today, self.tomorrow]):
            self.create_voice_usage(sub_sprint, 1, usage, date)

        return sub_att, sub_sprint
