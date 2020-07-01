from wt.tests import BaseAPITestCase
from wt.usage.models import AggregatedDataUsageRecord, AggregatedVoiceUsageRecord, DataUsageRecord, VoiceUsageRecord


class PopulateTestCase(BaseAPITestCase):
    def test_correct(self):
        # create subscriptions and usages
        sub_att, sub_sprint = self.create_basic_test_set()

        # test data usage
        AggregatedDataUsageRecord.populate(self.today.date())
        # test that counted raw records have been deleted
        self.assertEqual(DataUsageRecord.objects.count(), 2)

        self.assertEqual(AggregatedDataUsageRecord.objects.count(), 1)
        att_record = AggregatedDataUsageRecord.objects.get()
        self.assertEqual(att_record.kilobytes_used, 101)
        self.assertEqual(att_record.price, 2)

        # test duplicate call to be sure
        AggregatedDataUsageRecord.populate(self.today)
        self.assertEqual(DataUsageRecord.objects.count(), 2)
        self.assertEqual(AggregatedDataUsageRecord.objects.count(), 1)
        # and assertions...
        att_record.refresh_from_db()
        self.assertEqual(att_record.kilobytes_used, 101)
        self.assertEqual(att_record.price, 2)

        # test voice
        AggregatedVoiceUsageRecord.populate(self.today.date())
        self.assertEqual(VoiceUsageRecord.objects.count(), 2)
        self.assertEqual(AggregatedVoiceUsageRecord.objects.count(), 2)

        att_record = AggregatedVoiceUsageRecord.objects.get(att_subscription=sub_att)
        self.assertEqual(att_record.seconds_used, 5)
        self.assertEqual(att_record.price, 1)

        sprint_record = AggregatedVoiceUsageRecord.objects.get(sprint_subscription=sub_sprint)
        self.assertEqual(sprint_record.seconds_used, 20)
        self.assertEqual(sprint_record.price, 1)

        # now add new record
        sub = self.create_att()
        self.create_data_usage(sub, '1.01', 101, self.today)
        self.assertEqual(DataUsageRecord.objects.count(), 3)
        AggregatedDataUsageRecord.populate(self.today.date())

        self.assertEqual(AggregatedDataUsageRecord.objects.count(), 2)
        self.assertEqual(DataUsageRecord.objects.count(), 2)
        # test price and usage for new record
        record = AggregatedDataUsageRecord.objects.get(att_subscription=sub)
        self.assertEqual(str(record.price), '1.01')
        self.assertEqual(record.kilobytes_used, 101)

        # and test that other records stay ok
        att_record.refresh_from_db()
        self.assertEqual(str(att_record.price), '1.00')
