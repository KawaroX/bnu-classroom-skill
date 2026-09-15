"""Offline behavior tests; never connect to the school service."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import URLError

spec = importlib.util.spec_from_file_location('classroom', Path(__file__).parents[1] / 'scripts/bnu_classroom.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ClassroomTests(unittest.TestCase):
    def run_query(self, args, data=None, error=None):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(app, 'build_opener') as factory:
            if error:
                factory.return_value.open.side_effect = error
            else:
                factory.return_value.open.return_value = io.StringIO(json.dumps(data))
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = app.main(args)
            return code, out.getvalue(), err.getvalue(), factory

    def test_json_and_text_filter_all_slots(self):
        rows = [{'room_number': '101', 'status': [0, 0, 0, 0, 0, 1]},
                {'room_number': '102', 'status': [1, 1, 1, 1, 0, 0]}]
        data = {'success': 1, 'result': rows}
        code, output, _, _ = self.run_query(['--json', '--free-slots', '5', '6'], data)
        result = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(result['result'], rows[1:])
        self.assertEqual((result['total_count'], result['count']), (2, 1))
        _, text, _, _ = self.run_query(['--free-slots', '5', '6'], data)
        self.assertIn('102\t', text)
        self.assertNotIn('101\t', text)

    def test_room_dates_and_endpoint(self):
        rows = [{'date': '2026-09-15', 'status': [0] * 6},
                {'date': '2026-09-16', 'status': [1] * 6}]
        code, output, _, factory = self.run_query(['--room', '307', '--json', '--free-slots', '1'],
                                                 {'success': 1, 'detail': rows})
        result = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(result['detail'], rows[:1])
        self.assertIsNone(result['query_date'])
        url = factory.return_value.open.call_args.args[0].full_url
        self.assertIn('room-detail.php?', url)
        self.assertIn('room=307', url)
        self.assertNotIn('time=', url)

    def test_bad_data_fails_instead_of_returning_zero(self):
        invalid = [{'success': 1}, {'success': 0}, {'success': 1, 'result': None},
                   {'success': 1, 'result': [{'room_number': '101', 'status': [0]}]},
                   {'success': 1, 'result': [{'room_number': '101', 'status': ['0'] * 6}]},
                   {'success': 1, 'result': [{'status': [0] * 6}]}]
        for data in invalid:
            with self.subTest(data=data):
                code, output, err, _ = self.run_query(['--json'], data)
                self.assertEqual(code, 1)
                self.assertEqual(json.loads(output)['success'], 0)
                self.assertIn('查询失败', err)

    def test_empty_and_no_match_are_distinguishable(self):
        for rows, total in [([], 0), ([{'room_number': '101', 'status': [1] * 6}], 1)]:
            code, output, _, _ = self.run_query(['--json', '--free-slots', '1'], {'success': 1, 'result': rows})
            result = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual((result['total_count'], result['count']), (total, 0))

    def test_network_error(self):
        code, output, err, _ = self.run_query(['--json'], error=URLError('offline'))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output)['success'], 0)
        self.assertIn('offline', err)

    def test_list_buildings_without_network(self):
        code, output, _, factory = self.run_query(['--list-buildings', '--json'])
        self.assertEqual(code, 0)
        self.assertIn('教二楼', json.loads(output)['buildings'])
        factory.assert_not_called()

    def test_invalid_arguments_do_not_request_network(self):
        for args in [['--room', '307', '--day', 'today'], ['--building', '不存在'],
                     ['--room', ' '], ['--free-slots', '7']]:
            with self.subTest(args=args), patch.object(app, 'build_opener') as factory:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    app.main(args)
                self.assertEqual(exc.exception.code, 2)
                factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
