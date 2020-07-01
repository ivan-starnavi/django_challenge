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
        # create subscriptions and usages
        sub_att, sub_sprint = self.create_basic_test_set()

        response = self.client.post(self.url, data={'limit': 2})
        self.assertEqual(response.status_code, 200)

        correct_response = [
            {
                'id': sub_att.id,
                'data_usage_exceeds': '1.00',  # 3 usages
                'voice_usage_exceeds': None,  # 1 usage
                'subscription_type': 'ATTSubscription'
            },
            {
                'id': sub_sprint.id,
                'data_usage_exceeds': None,  # 1 usage
                'voice_usage_exceeds': '1.00',  # 3 usages
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
        # create subscriptions and usages
        sub_att, sub_sprint = self.create_basic_test_set()

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
            ('data', self.today, today_data_correct),
            ('data', self.tomorrow, tomorrow_data_correct),
            ('voice', self.today, today_voice_correct),
            ('voice', self.tomorrow, tomorrow_voice_correct)
        ]
        for usage_type, date, correct in test:
            response = self.send(usage_type, date, date)
            self.assertEqual(response.status_code, 200)
            self.check_response(correct, response.json())

        # add one more
        sub = self.create_sprint()
        self.create_data_usage(sub, '100.01', 1, self.tomorrow)
        response = self.send('data', self.tomorrow, self.tomorrow)
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
        response = self.send('data', self.tomorrow, self.today)
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

        for func in [self.create_att, self.create_sprint]:
            for _ in range(subs_count):
                sub = func()
                for idx in range(usages_count):
                    self.create_data_usage(sub, '1.01', 1, self.today if idx % 2 else self.tomorrow)
                    self.create_voice_usage(sub, '1.01', 1, self.tomorrow if idx % 2 else self.today)

        response = self.send('data', self.today, self.today).json()
        self.assertEqual(len(response), subs_count * 2)  # 2 = att + sprint
        for obj in response:
            self.assertEqual(obj['usage'], usages_count // 2, obj)
            self.assertAlmostEqual(float(obj['price']), 1.01 * usages_count / 2, 2)

        # test from today to tomorrow
        response = self.send('voice', self.today, self.tomorrow).json()
        self.assertEqual(len(response), subs_count * 2)  # 2 = att + sprint
        for obj in response:
            self.assertEqual(obj['usage'], usages_count, obj)
            self.assertAlmostEqual(float(obj['price']), 1.01 * usages_count, 2)
