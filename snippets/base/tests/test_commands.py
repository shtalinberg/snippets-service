from datetime import date, datetime, timedelta

from unittest.mock import ANY, DEFAULT, Mock, call, patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Q
from django.test.utils import override_settings

from snippets.base import models
from snippets.base.management.commands import fetch_daily_metrics
from snippets.base.tests import (DistributionFactory, DistributionBundleFactory, JobFactory,
                                 SnippetFactory, TargetFactory, TestCase)


class DisableSnippetsPastPublishDateTests(TestCase):
    def test_base(self):
        snippet_without_end_date = SnippetFactory(published=True, publish_end=None)
        snippet_that_has_ended = SnippetFactory(published=True, publish_end=datetime.utcnow())
        snippet_ending_in_the_future = SnippetFactory(
            published=True, publish_end=datetime.utcnow() + timedelta(days=1))

        call_command('disable_snippets_past_publish_date', stdout=Mock())

        snippet_without_end_date.refresh_from_db()
        snippet_that_has_ended.refresh_from_db()
        snippet_ending_in_the_future.refresh_from_db()

        self.assertFalse(snippet_that_has_ended.published)
        self.assertTrue(snippet_without_end_date.published)
        self.assertTrue(snippet_ending_in_the_future.published)


@override_settings(REDASH_API_KEY='secret')
class FetchMetricsTests(TestCase):
    def test_base(self):
        job_running = JobFactory(
            status=models.Job.PUBLISHED,
            publish_start='2050-01-05 01:00',
            publish_end='2050-01-08 02:00',
            limit_impressions=1000,
        )
        # Without end date
        job_running2 = JobFactory(
            status=models.Job.PUBLISHED,
            publish_start='2050-01-04 01:00',
            publish_end=None,
            limit_blocks=1000,
        )
        request_data_first = {
            'start_date': '2050-01-05',
            'end_date': '2050-01-06',
            'message_id': job_running.id,
        }
        request_data_second = {
            'start_date': '2050-01-04',
            'end_date': '2050-01-06',
            'message_id': job_running2.id,
        }
        return_data_first = {
            'query_result': {
                'data': {
                    'rows': [
                        {
                            'event': 'IMPRESSION',
                            'counts': 100,
                        },
                        {
                            'event': 'BLOCK',
                            'counts': 10,
                        },
                        {
                            'event': 'CLICK',
                            'counts': 50,
                        },
                        {
                            'event': 'CLICK_BUTTON',
                            'counts': 60,
                        }
                    ]
                }
            }
        }
        return_data_second = {
            'query_result': {
                'data': {
                    'rows': [
                        {
                            'event': 'IMPRESSION',
                            'counts': 250,
                        },
                        {
                            'event': 'BLOCK',
                            'counts': 100,
                        },
                        {
                            'event': 'CLICK',
                            'counts': 25,
                        },
                        {
                            'event': 'CLICK_BUTTON',
                            'counts': 10,
                        }
                    ]
                }
            }
        }

        with patch('snippets.base.management.commands.fetch_metrics.RedashDynamicQuery') as rdq:
            with patch('snippets.base.management.commands.fetch_metrics.datetime', wraps=datetime) as datetime_mock:  # noqa
                datetime_mock.utcnow.return_value = datetime(2050, 1, 6)
                rdq.return_value.query.side_effect = [
                    return_data_first, return_data_second
                ]
                call_command('fetch_metrics', stdout=Mock())

        rdq.return_value.query.assert_has_calls([
            call(settings.REDASH_JOB_QUERY_BIGQUERY_ID, request_data_first),
            call(settings.REDASH_JOB_QUERY_BIGQUERY_ID, request_data_second),
        ])

        job_running.refresh_from_db()
        self.assertEqual(job_running.metric_impressions, 100)
        self.assertEqual(job_running.metric_blocks, 10)
        self.assertEqual(job_running.metric_clicks, 110)

        job_running2.refresh_from_db()
        self.assertEqual(job_running2.metric_impressions, 250)
        self.assertEqual(job_running2.metric_blocks, 100)
        self.assertEqual(job_running2.metric_clicks, 35)

    def test_no_data_fetched(self):
        JobFactory(
            status=models.Job.PUBLISHED,
            publish_start='2050-01-05 01:00',
            publish_end='2050-01-06 02:00',
            limit_clicks=1000,
        )

        # Error raised while fetch Telemetry Data
        with patch('snippets.base.management.commands.fetch_metrics.RedashDynamicQuery') as rdq:
            rdq.return_value.query.side_effect = Exception('error')
            self.assertRaises(CommandError, call_command, 'fetch_metrics', stdout=Mock())

        # Error raised while processing empty Telemetry Data
        return_data = {
            'query_result': {}
        }
        with patch('snippets.base.management.commands.fetch_metrics.RedashDynamicQuery') as rdq:
            rdq.return_value.query.return_value = return_data
            self.assertRaises(CommandError, call_command, 'fetch_metrics', stdout=Mock())


class UpdateJobsTests(TestCase):
    @override_settings(SNIPPETS_PUBLICATION_OFFSET=5)
    def test_base(self):
        now = datetime.utcnow()
        job_without_end_date = JobFactory(
            status=models.Job.PUBLISHED,
            publish_end=None)
        job_that_has_ended = JobFactory(
            status=models.Job.PUBLISHED,
            publish_end=now)
        job_ending_in_the_future = JobFactory(
            status=models.Job.PUBLISHED,
            limit_impressions=10000,
            metric_last_update=now,
            publish_end=now + timedelta(days=1))
        job_scheduled_not_ready_to_go = JobFactory(
            status=models.Job.SCHEDULED,
            publish_start=now)
        job_scheduled_ready_to_go = JobFactory(
            status=models.Job.SCHEDULED,
            publish_start=now - timedelta(minutes=10))
        job_scheduled_in_the_future = JobFactory(
            status=models.Job.SCHEDULED,
            publish_start=now + timedelta(days=1))
        job_impression_limit_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_impressions=10000,
            metric_impressions=10000,
            metric_last_update=now,
            publish_end=now + timedelta(days=1))
        job_click_limit_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_impressions=10000,
            metric_impressions=1000,
            limit_clicks=1000,
            metric_clicks=1001,
            metric_last_update=now,
            publish_end=now + timedelta(days=1))
        job_block_limit_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_blocks=10,
            metric_blocks=1000,
            metric_last_update=now - timedelta(minutes=30),
            publish_end=now + timedelta(days=1)
        )
        job_impression_limit_not_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_impressions=100,
            metric_impressions=10,
            metric_last_update=now - timedelta(hours=12),
            publish_end=now + timedelta(days=1))
        job_click_limit_not_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_clicks=100,
            metric_clicks=10,
            metric_last_update=now - timedelta(hours=1),
            publish_end=now + timedelta(days=1))
        job_block_limit_not_reached = JobFactory(
            status=models.Job.PUBLISHED,
            limit_blocks=100,
            metric_blocks=10,
            metric_last_update=now,
            publish_end=now + timedelta(days=1))
        job_impression_limit_not_reached_but_no_data = JobFactory(
            status=models.Job.PUBLISHED,
            limit_impressions=100,
            metric_impressions=10,
            metric_last_update=now - timedelta(hours=26),
            publish_end=now + timedelta(days=1))
        job_click_limit_not_reached_but_no_data = JobFactory(
            status=models.Job.PUBLISHED,
            limit_clicks=100,
            metric_clicks=10,
            metric_last_update=now - timedelta(hours=30),
            publish_end=now + timedelta(days=1))
        job_block_limit_not_reached_but_no_data = JobFactory(
            status=models.Job.PUBLISHED,
            limit_blocks=100,
            metric_blocks=10,
            metric_last_update=now - timedelta(hours=40),
            publish_end=now + timedelta(days=1))
        job_block_limit_not_reached_just_created = JobFactory(
            status=models.Job.PUBLISHED,
            limit_blocks=100,
            metric_blocks=10,
            publish_end=now + timedelta(days=1))

        job_cancelled = JobFactory(status=models.Job.CANCELED)
        job_completed = JobFactory(status=models.Job.COMPLETED)

        call_command('update_jobs', stdout=Mock())

        job_without_end_date.refresh_from_db()
        job_that_has_ended.refresh_from_db()
        job_ending_in_the_future.refresh_from_db()
        job_scheduled_not_ready_to_go.refresh_from_db()
        job_scheduled_ready_to_go.refresh_from_db()
        job_scheduled_in_the_future.refresh_from_db()
        job_cancelled.refresh_from_db()
        job_completed.refresh_from_db()
        job_impression_limit_reached.refresh_from_db()
        job_click_limit_reached.refresh_from_db()
        job_block_limit_reached.refresh_from_db()
        job_impression_limit_not_reached.refresh_from_db()
        job_click_limit_not_reached.refresh_from_db()
        job_block_limit_not_reached.refresh_from_db()
        job_impression_limit_not_reached_but_no_data.refresh_from_db()
        job_click_limit_not_reached_but_no_data.refresh_from_db()
        job_block_limit_not_reached_but_no_data.refresh_from_db()
        job_block_limit_not_reached_just_created.refresh_from_db()

        self.assertEqual(job_without_end_date.status, models.Job.PUBLISHED)
        self.assertEqual(job_that_has_ended.status, models.Job.COMPLETED)
        self.assertEqual(job_ending_in_the_future.status, models.Job.PUBLISHED)
        self.assertEqual(job_scheduled_not_ready_to_go.status, models.Job.SCHEDULED)
        self.assertEqual(job_scheduled_ready_to_go.status, models.Job.PUBLISHED)
        self.assertEqual(job_scheduled_in_the_future.status, models.Job.SCHEDULED)
        self.assertEqual(job_cancelled.status, models.Job.CANCELED)
        self.assertEqual(job_completed.status, models.Job.COMPLETED)
        self.assertEqual(job_impression_limit_reached.status, models.Job.COMPLETED)
        self.assertEqual(job_click_limit_reached.status, models.Job.COMPLETED)
        self.assertEqual(job_block_limit_reached.status, models.Job.COMPLETED)
        self.assertEqual(job_impression_limit_not_reached.status, models.Job.PUBLISHED)
        self.assertEqual(job_click_limit_not_reached.status, models.Job.PUBLISHED)
        self.assertEqual(job_block_limit_not_reached.status, models.Job.PUBLISHED)
        self.assertEqual(job_impression_limit_not_reached_but_no_data.status, models.Job.COMPLETED)
        self.assertEqual(job_click_limit_not_reached_but_no_data.status, models.Job.COMPLETED)
        self.assertEqual(job_block_limit_not_reached_but_no_data.status, models.Job.COMPLETED)
        self.assertEqual(job_block_limit_not_reached_just_created.status, models.Job.PUBLISHED)


class GenerateBundlesTests(TestCase):
    def setUp(self):
        self.distribution = DistributionFactory.create(name='Default')
        self.distribution_bundle = DistributionBundleFactory.create(name='Default',
                                                                    code_name='default')
        self.distribution_bundle.distributions.add(self.distribution)

    def test_generate_all(self):
        with patch('snippets.base.management.commands.generate_bundles.Job') as job_mock:
            job_mock.objects.all.return_value = models.Job.objects.none()
            call_command('generate_bundles', stdout=Mock())
        job_mock.objects.all.assert_called()
        job_mock.objects.filter.assert_not_called()

    def test_generate_after_timestamp(self):
        with patch('snippets.base.management.commands.generate_bundles.Job') as job_mock:
            job_mock.objects.filter.return_value = models.Job.objects.none()
            call_command('generate_bundles', timestamp='2019-01-01', stdout=Mock())
        job_mock.objects.all.assert_not_called()
        job_mock.objects.filter.assert_called_with(
            Q(snippet__modified__gte='2019-01-01') |
            Q(distribution__distributionbundle__modified__gte='2019-01-01')
        )

    @override_settings(MEDIA_BUNDLES_PREGEN_ROOT='pregen')
    def test_generation(self):
        target = TargetFactory(
            on_release=True, on_beta=True, on_nightly=False, on_esr=False, on_aurora=False
        )
        # Draft, completed, scheduled or cancelled
        JobFactory(
            status=models.Job.DRAFT,
            snippet__locale=',en,',
            targets=[target],
        )
        JobFactory(
            status=models.Job.COMPLETED,
            snippet__locale=',en,',
            targets=[target],
        )
        JobFactory(
            status=models.Job.SCHEDULED,
            snippet__locale=',en,',
            targets=[target],
        )
        JobFactory(
            status=models.Job.CANCELED,
            snippet__locale=',en,',
            targets=[target],
        )
        JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[target],
            distribution__name='not-default',
        )

        # Jobs to be included in the bundle
        published_job_1 = JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[target],
        )
        published_job_2 = JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[target],
            distribution__name='other-distribution-part-of-default-bundle',
        )

        # Add Distribution to the Default DistributionBundle
        models.DistributionBundle.objects.get(name='Default').distributions.add(
            models.Distribution.objects.get(name='other-distribution-part-of-default-bundle')
        )

        with patch.multiple('snippets.base.management.commands.generate_bundles',
                            json=DEFAULT,
                            product_details=DEFAULT,
                            default_storage=DEFAULT) as mock:
            mock['json'].dumps.return_value = ''
            mock['product_details'].languages.keys.return_value = ['fr', 'en-us', 'en-au']
            call_command('generate_bundles', stdout=Mock())

        self.assertEqual(mock['default_storage'].save.call_count, 4)

        mock['default_storage'].save.assert_has_calls([
            call('pregen/Firefox/release/en-us/default.json', ANY),
            call('pregen/Firefox/release/en-au/default.json', ANY),
            call('pregen/Firefox/beta/en-us/default.json', ANY),
            call('pregen/Firefox/beta/en-au/default.json', ANY),
        ], any_order=True)

        # Check that there's only one job included in the bundle and that it's
        # the correct one.
        self.assertEqual(
            len(mock['json'].dumps.call_args_list[0][0][0]['messages']),
            2
        )
        self.assertEqual(
            set([mock['json'].dumps.call_args_list[0][0][0]['messages'][0]['id'],
                 mock['json'].dumps.call_args_list[0][0][0]['messages'][1]['id']]),
            set([str(published_job_1.id), str(published_job_2.id)])
        )

    @override_settings(
        MEDIA_BUNDLES_PREGEN_ROOT='pregen',
        NIGHTLY_INCLUDES_RELEASE=True,
    )
    def test_nightly_includes_release(self):
        release_job = JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[
                TargetFactory(
                    on_release=True, on_beta=True, on_nightly=False, on_esr=False, on_aurora=False)
            ]
        )
        nightly_job = JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[
                TargetFactory(
                    on_release=True, on_beta=False, on_nightly=True, on_esr=False, on_aurora=False)
            ]
        )

        # Beta only job, not to be included
        JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',en,',
            targets=[
                TargetFactory(
                    on_release=False, on_beta=True, on_nightly=False, on_esr=False, on_aurora=False)
            ]
        )

        with patch.multiple('snippets.base.management.commands.generate_bundles',
                            json=DEFAULT,
                            product_details=DEFAULT,
                            default_storage=DEFAULT) as mock:
            mock['json'].dumps.return_value = ''
            mock['product_details'].languages.keys.return_value = ['en-us']
            call_command('generate_bundles', stdout=Mock())

        # Loop to find the nighlty bundle
        for arg_list in mock['json'].dumps.call_args_list:
            if arg_list[0][0]['metadata']['channel'] == 'nightly':
                self.assertEqual(
                    len(arg_list[0][0]['messages']),
                    2
                )
                self.assertEqual(
                    set([arg_list[0][0]['messages'][0]['id'],
                         arg_list[0][0]['messages'][1]['id']]),
                    set([str(release_job.id), str(nightly_job.id)])
                )
                self.assertEqual(
                    set([arg_list[0][0]['messages'][0]['targeting'],
                         arg_list[0][0]['messages'][1]['targeting']]),
                    set(['', 'false'])
                )

    @override_settings(BUNDLE_BROTLI_COMPRESS=True)
    def test_brotli_called(self):
        with patch('snippets.base.management.commands.generate_bundles.brotli') as brotli_mock:
            brotli_mock.compress.return_value = ''
            self.test_generation()
        brotli_mock.compress.assert_called()

    @override_settings(BUNDLE_BROTLI_COMPRESS=False)
    def test_no_brotli(self):
        with patch('snippets.base.management.commands.generate_bundles.brotli') as brotli_mock:
            self.test_generation()
        brotli_mock.compress.assert_not_called()

    @override_settings(MEDIA_BUNDLES_PREGEN_ROOT='pregen')
    def test_delete(self):
        distribution = DistributionFactory()
        distribution_bundle = DistributionBundleFactory(
            code_name='foo',
            enabled=False,
        )
        distribution_bundle.distributions.add(distribution)

        target = TargetFactory(
            on_release=False, on_beta=False, on_nightly=True, on_esr=False, on_aurora=False
        )
        JobFactory(
            status=models.Job.COMPLETED,
            snippet__locale=',fr,',
            targets=[target],
        )

        # Still published, but belongs to a disabled distribution
        JobFactory(
            status=models.Job.PUBLISHED,
            snippet__locale=',fr,',
            targets=[target],
            distribution=distribution,
        )

        with patch('snippets.base.management.commands.generate_bundles.default_storage') as ds_mock:
            # Test that only removes if file exists.
            ds_mock.exists.return_value = True
            call_command('generate_bundles', stdout=Mock())

        ds_mock.delete.assert_has_calls([
            call('pregen/Firefox/nightly/fr/default.json'),
            call('pregen/Firefox/nightly/fr/foo.json')
        ])
        ds_mock.save.assert_not_called()

    def test_delete_does_not_exist(self):
        target = TargetFactory(
            on_release=False, on_beta=False, on_nightly=True, on_esr=False, on_aurora=False
        )
        JobFactory(
            status=models.Job.COMPLETED,
            snippet__locale=',fr,',
            targets=[target],
        )

        with patch('snippets.base.management.commands.generate_bundles.default_storage') as ds_mock:
            # Test that only removes if file exists.
            ds_mock.exists.return_value = False
            call_command('generate_bundles', stdout=Mock())

        ds_mock.delete.assert_not_called()
        ds_mock.save.assert_not_called()


@override_settings(REDASH_API_KEY='secret')
class FetchDailyMetricsTests(TestCase):
    def test_base(self):
        with patch('snippets.base.management.commands.fetch_daily_metrics.etl') as etl_mock:
            etl_mock.update_impressions.return_value = True
            etl_mock.update_job_metrics.return_value = True

            call_command('fetch_daily_metrics', date='2050-01-05', stdout=Mock())

        etl_mock.update_impressions.assert_called()
        etl_mock.update_impressions.call_args[0][0] == date(2050, 1, 5)

        etl_mock.update_job_metrics.assert_called()
        etl_mock.update_job_metrics.call_args[0][0] == date(2050, 1, 5)

    def test_no_data_fetched(self):
        # Error raised while processing empty Telemetry Data
        with patch('snippets.base.management.commands.fetch_daily_metrics.etl') as etl_mock:
            etl_mock.update_impressions.return_value = False
            etl_mock.update_job_metrics.return_value = True

            self.assertRaises(CommandError, call_command, 'fetch_daily_metrics',
                              date='2050-01-05', stdout=Mock())

    def test_fetch_all_missing_dates(self):
        three_days_ago = date.today() - timedelta(days=3)
        two_days_ago = date.today() - timedelta(days=2)
        yesterday = date.today() - timedelta(days=1)

        # Assume that we have data for yesterday but not for before
        # that.
        models.JobDailyPerformance.objects.create(job=JobFactory(), date=yesterday)

        with patch('snippets.base.management.commands.fetch_daily_metrics.etl') as etl_mock:
            with patch.object(fetch_daily_metrics, 'METRICS_START_DATE', new=three_days_ago):
                etl_mock.update_impressions.return_value = True
                etl_mock.update_job_metrics.return_value = True
                call_command('fetch_daily_metrics', stdout=Mock())

        self.assertEqual(len(etl_mock.update_impressions.mock_calls), 2)
        self.assertEqual(len(etl_mock.update_job_metrics.mock_calls), 2)

        etl_mock.update_impressions.has_calls(
            [call(two_days_ago), call(three_days_ago)], any_order=True
        )
        etl_mock.update_job_metrics.has_calls(
            [call(two_days_ago), call(three_days_ago)], any_order=True
        )
