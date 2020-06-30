from datetime import timedelta

from django.utils import timezone
from rest_framework.reverse import reverse

from wt.tests import BaseAPITestCase


class BaseStatsTestCase(BaseAPITestCase):
    def check_response(self, correct, response):
        for resp in correct:
            self.assertIn(resp, response)
        self.assertEqual(len(correct), len(response))


class StatsExceedingTestCase(BaseStatsTestCase):
    url = reverse('stats-exceeded')

    def test_correct(self):
        # create subscriptions
        sub_att = self.create_att()
        sub_sprint = self.create_sprint()

        # create usages
        #   att
        for price in [1, 10, 100]:
            self.create_data_usage(sub_att, price, 0)
        self.create_voice_usage(sub_att, 5, 0)
        #   sprint
        self.create_data_usage(sub_sprint, 0, 0)
        for price in [2, 20, 200]:
            self.create_data_usage(sub_sprint, price, 0)

        response = self.client.post(self.url, data={'limit': 2})
        self.assertEqual(response.status_code, 200)

        correct_response = [
            {
                'id': sub_att.id,
                'data_usage_exceeds': '109.00',  # 111 - 2
                'voice_usage_exceeds': '3.00',  # 5 - 2
                'subscription_type': 'ATTSubscription'
            },
            {
                'id': sub_sprint.id,
                'data_usage_exceeds': '220.00',  # 222 - 2
                'voice_usage_exceeds': None,  # 0 - 2 -> no exceeding
                'subscription_type': 'SprintSubscription'
            }
        ]
        self.check_response(correct_response, response.json())

        # add another
        sub_sprint_2 = self.create_sprint()
        self.create_voice_usage(sub_sprint_2, '2.01', 0)

        response = self.client.post(self.url, data={'limit': 2})

        # and check it
        correct_response.append({
            'id': sub_sprint_2.id,
            'data_usage_exceeds': None,
            'voice_usage_exceeds': '0.01',
            'subscription_type': 'SprintSubscription'
        })
        self.check_response(correct_response, response.json())

    def test_many(self):
        subs_count = 20
        usages_count = 10
        limit = 2

        for func in [self.create_att, self.create_sprint]:
            for _ in range(subs_count):
                sub = func()
                for _ in range(usages_count):
                    self.create_data_usage(sub, 10, 10)
                    self.create_voice_usage(sub, 10, 10)

        response = self.client.post(self.url, data={'limit': limit}).json()
        self.assertEqual(len(response), subs_count * 2)  # 2 = functions count
        self.assertTrue(
            all(
                map(
                    lambda obj: obj['data_usage_exceeds'] == f'{10 * usages_count - limit}.00' and
                                obj['voice_usage_exceeds'] == f'{10 * usages_count - limit}.00',
                    response
                )
            )
        )

    def test_incorrect_request(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'limit': ['This field is required.']})

        response = self.client.post(self.url, data={'limit': 'test_incorrect'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'limit': ['A valid number is required.']})


class UsageMetricsTestCase(BaseStatsTestCase):
    url = reverse('stats-usage-metrics')

    def send(self, usage_type, from_date, to_date):
        return self.client.post(self.url, {'usage_type': usage_type, 'from_date': from_date, 'to_date': to_date})

    def test_correct(self):
        today = timezone.now()
        tomorrow = today + timedelta(days=1)

        # create subscriptions
        sub_att = self.create_att()
        sub_sprint = self.create_sprint()

        # create usages
        #   att
        for usage, date in zip([1, 10, 100], [today, tomorrow, today]):
            self.create_data_usage(sub_att, 1, usage, date)
        self.create_voice_usage(sub_att, 1, 5, today)
        #   sprint
        self.create_data_usage(sub_sprint, 1, 5, tomorrow)
        for usage, date in zip([2, 20, 200], [tomorrow, today, tomorrow]):
            self.create_voice_usage(sub_sprint, 1, usage, date)

        # correct responses
        today_data_correct = [
            {
                'subscription_type': 'ATT',
                'subscription_id': sub_att.id,
                'usage': 101,
                'price': '2.00'
            }
        ]
        tomorrow_data_correct = [
            {
                'subscription_type': 'ATT',
                'subscription_id': sub_att.id,
                'usage': 10,
                'price': '1.00'
            },
            {
                'subscription_type': 'Sprint',
                'subscription_id': sub_sprint.id,
                'usage': 5,
                'price': '1.00'
            }
        ]
        today_voice_correct = [
            {
                'subscription_type': 'ATT',
                'subscription_id': sub_att.id,
                'usage': 5,
                'price': '1.00'
            },
            {
                'subscription_type': 'Sprint',
                'subscription_id': sub_sprint.id,
                'usage': 20,
                'price': '1.00'
            }
        ]
        tomorrow_voice_correct = [
            {
                'subscription_type': 'Sprint',
                'subscription_id': sub_sprint.id,
                'usage': 202,
                'price': '2.00'
            }
        ]

        test = [
            ('data', today, today_data_correct),
            ('data', tomorrow, tomorrow_data_correct),
            ('voice', today, today_voice_correct),
            ('voice', tomorrow, tomorrow_voice_correct)
        ]
        for usage_type, date, correct in test:
            response = self.send(usage_type, date, date)
            self.assertEqual(response.status_code, 200)
            self.check_response(correct, response.json())

        # add one more
        sub = self.create_sprint()
        self.create_data_usage(sub, '100.01', 1, tomorrow)
        response = self.send('data', tomorrow, tomorrow)
        tomorrow_data_correct.append(
            {
                'subscription_type': 'Sprint',
                'subscription_id': sub.id,
                'usage': 1,
                'price': '100.01'
            }
        )
        self.check_response(tomorrow_data_correct, response.json())

        # send dates that don't form an interval
        response = self.send('data', tomorrow, today)
        self.check_response([], response.json())

    def test_incorrect(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()), {'usage_type', 'from_date', 'to_date'})

        response = self.client.post(self.url, data={'usage_type': 'test', 'from_date': 'test', 'to_date': 'test'})
        self.assertEqual(response.status_code, 400)
        datetime_error = 'Datetime has wrong format. Use one of these formats instead: ' \
                         'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
        self.assertEqual(
            response.json(),
            {
                'usage_type': ['"test" is not a valid choice.'],
                'to_date': [datetime_error],
                'from_date': [datetime_error],
            }
        )

    def test_many(self):
        subs_count = 20
        usages_count = 10

        today = timezone.now()
        tomorrow = today + timedelta(days=1)

        for func in [self.create_att, self.create_sprint]:
            for _ in range(subs_count):
                sub = func()
                for idx in range(usages_count):
                    self.create_data_usage(sub, '1.01', 1, today if idx % 2 else tomorrow)
                    self.create_voice_usage(sub, '1.01', 1, tomorrow if idx % 2 else today)

        response = self.send('data', today, today).json()
        self.assertEqual(len(response), subs_count * 2)  # 2 = att + sprint
        for obj in response:
            self.assertEqual(obj['usage'], usages_count // 2, obj)
            self.assertAlmostEqual(float(obj['price']), 1.01 * usages_count / 2, 2)

        # test from today to tomorrow
        response = self.send('voice', today, tomorrow).json()
        self.assertEqual(len(response), subs_count * 2)  # 2 = att + sprint
        for obj in response:
            self.assertEqual(obj['usage'], usages_count, obj)
            self.assertAlmostEqual(float(obj['price']), 1.01 * usages_count, 2)
