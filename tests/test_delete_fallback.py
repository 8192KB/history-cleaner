import unittest
from unittest.mock import Mock

from dcinside_cleaner import Cleaner


def _entry():
    return {
        'log_no': '10',
        'gallery': 'test',
        'no': '20',
        'cno': '0',
    }


class DeleteFallbackTest(unittest.TestCase):
    def setUp(self):
        self.cleaner = Cleaner()
        self.cleaner.user_id = 'user'
        self.cleaner.delay = 0
        self.cleaner.gallog_delay = 0
        self.cleaner.app_api = Mock()
        self.cleaner.app_api.isReady.return_value = True

    def test_app_blocked_captcha_is_solved_then_app_is_retried(self):
        self.cleaner.post_list = [_entry()]
        self.cleaner._deleteViaAppApi = Mock(side_effect=['BLOCKED', {}])
        self.cleaner.mobile.hasCaptcha = Mock(return_value=True)
        self.cleaner.solveCaptchaAuto = Mock(return_value={
            'solved': True,
            'attempts': 1,
            'code': 'abcd',
        })
        self.cleaner._deleteViaMobileGallog = Mock()
        self.cleaner._deleteViaGallog = Mock()

        events = list(self.cleaner.deletePosts('posting'))

        self.assertEqual(self.cleaner._deleteViaAppApi.call_count, 2)
        self.cleaner._deleteViaMobileGallog.assert_not_called()
        self.cleaner._deleteViaGallog.assert_not_called()
        self.assertIn('captcha_solving', [event['data'] for event in events
                                          if not event['status']])
        self.assertEqual(len([event for event in events if event['status']]), 1)

    def test_app_blocked_without_captcha_falls_back_mobile_then_desktop(self):
        self.cleaner.post_list = [_entry()]
        self.cleaner._deleteViaAppApi = Mock(return_value='BLOCKED')
        self.cleaner.mobile.hasCaptcha = Mock(return_value=False)
        self.cleaner._deleteViaMobileGallog = Mock(return_value={
            'result': 'fail',
            'msg': 'BLOCKED',
        })
        self.cleaner._deleteViaGallog = Mock(return_value={})

        events = list(self.cleaner.deletePosts('posting'))

        self.cleaner._deleteViaAppApi.assert_called_once()
        self.cleaner._deleteViaMobileGallog.assert_called_once_with('10')
        self.cleaner._deleteViaGallog.assert_called_once_with(
            '10', 'posting', False)
        self.assertIn('drain_start', [event['data'] for event in events
                                      if not event['status']])
        self.assertEqual(len([event for event in events if event['status']]), 1)

    def test_item_failure_is_retried_once_after_other_app_items(self):
        first = _entry()
        second = _entry()
        first['cno'] = '30'
        second['log_no'] = '11'
        second['no'] = '21'
        second['cno'] = '31'
        self.cleaner.post_list = [first, second]
        self.cleaner._deleteViaAppApi = Mock(side_effect=[
            {'result': 'fail', 'msg': '삭제할 수 없습니다.'},
            {},
            {},
        ])
        self.cleaner._deleteViaMobileGallog = Mock()
        self.cleaner._deleteViaGallog = Mock()

        events = list(self.cleaner.deletePosts('comment'))

        attempted = [
            call.args[0]['log_no']
            for call in self.cleaner._deleteViaAppApi.call_args_list
        ]
        self.assertEqual(attempted, ['10', '11', '10'])
        self.cleaner._deleteViaMobileGallog.assert_not_called()
        self.cleaner._deleteViaGallog.assert_not_called()
        self.assertIn('app_retry_queued', [
            event['data'] for event in events if not event['status']])
        self.assertEqual(len([event for event in events if event['status']]), 2)

    def test_second_item_failure_falls_back_to_mobile(self):
        entry = _entry()
        self.cleaner.post_list = [entry]
        failure = {'result': 'fail', 'msg': '삭제할 수 없습니다.'}
        self.cleaner._deleteViaAppApi = Mock(side_effect=[failure, failure])
        self.cleaner._deleteViaMobileGallog = Mock(return_value={})
        self.cleaner._deleteViaGallog = Mock()

        events = list(self.cleaner.deletePosts('posting'))

        self.assertEqual(self.cleaner._deleteViaAppApi.call_count, 2)
        self.cleaner._deleteViaMobileGallog.assert_called_once_with('10')
        self.cleaner._deleteViaGallog.assert_not_called()
        self.assertIn('drain_start', [
            event['data'] for event in events if not event['status']])
        self.assertEqual(len([event for event in events if event['status']]), 1)

    def test_mobile_captcha_is_not_overwritten_by_desktop_block(self):
        entry = _entry()
        entry['_gallog_only'] = True
        self.cleaner._deleteViaMobileGallog = Mock(return_value='CAPTCHA')
        self.cleaner._deleteViaGallog = Mock(return_value='BLOCKED')

        result = self.cleaner.deletePost(
            entry, 'posting', solve_captcha=False, allow_gallog=True)

        self.assertEqual(result, 'CAPTCHA')
        self.cleaner._deleteViaGallog.assert_not_called()


if __name__ == '__main__':
    unittest.main()
