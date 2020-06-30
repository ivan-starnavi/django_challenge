from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from wt.att_subscriptions.models import ATTSubscription
from wt.plans.models import Plan
from wt.sprint_subscriptions.models import SprintSubscription


class BaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = get_user_model().objects.create_user(username='user', password='123')
        cls.plan = Plan.objects.create(name='test', price='1.00', data_available=100)

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
