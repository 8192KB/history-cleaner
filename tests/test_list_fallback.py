import unittest
from unittest.mock import Mock

from dcinside_cleaner import Cleaner


class ListFallbackTest(unittest.TestCase):
    def setUp(self):
        self.cleaner = Cleaner()
        self.cleaner.user_id = 'user'
        self.cleaner.delay = 0

    def test_mobile_middle_page_failure_restarts_with_desktop(self):
        mobile_entry = {'log_no': 'mobile', 'gall_code': '1'}
        desktop_entry = {'log_no': 'desktop', 'gallery': 'test', 'no': '20'}
        self.cleaner.mobile.fetchPage = Mock(side_effect=[
            {
                'last_page': 2,
                'entries': [mobile_entry],
            },
            None,
        ])
        self.cleaner.getPageCount = Mock(return_value=1)
        self.cleaner.getPostList = Mock(return_value=[desktop_entry])

        events = list(self.cleaner.aggregatePosts('', 'comment'))

        self.assertEqual(events[0]['data'], 'list_fallback')
        self.assertEqual(events[0]['from'], 'mobile web')
        self.assertEqual(events[0]['to'], 'desktop web')
        self.assertEqual(self.cleaner.post_list, [desktop_entry])
        self.cleaner.getPageCount.assert_called_once_with('', 'comment')

    def test_complete_mobile_collection_does_not_use_desktop(self):
        entries = [
            {'log_no': '1', 'gall_code': '1'},
            {'log_no': '2', 'gall_code': '1'},
        ]
        self.cleaner.mobile.fetchPage = Mock(side_effect=[
            {'last_page': 2, 'entries': [entries[0]]},
            {'last_page': 2, 'entries': [entries[1]]},
        ])
        self.cleaner.getPageCount = Mock()

        events = list(self.cleaner.aggregatePosts('', 'comment'))

        self.assertEqual(len(events), 2)
        self.assertTrue(all(event['status'] for event in events))
        self.assertCountEqual(self.cleaner.post_list, entries)
        self.cleaner.getPageCount.assert_not_called()


if __name__ == '__main__':
    unittest.main()
