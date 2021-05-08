from datetime import date, datetime
from http import HTTPStatus
from unittest import TestCase, mock
from uuid import uuid4

from app.akashi import (BREAK, CLOCK_IN, CLOCK_OUT, LEAVE_DIRECTLY, RESTART,
                        STRAIGHT_TO, AkashiRequestClient, APIError,
                        FetchedStampResponse, NewStampResponse,
                        ReissuedTokenResponse, RequestFailedError, Stamp,
                        annotate_stamp_type)

dummy_token = str(uuid4())


def get_stamp_response(*args, **kwargs):
    return mocked_response({
        'success': True,
        'response': {
            'login_company_code': '',
            'staff_id': 1,
            'count': 2,
            'stamps': [{
                'stamped_at': '2020/01/01 09:00:00',
                'type': CLOCK_IN
            }, {
                'stamped_at': '2020/01/01 18:00:00',
                'type': CLOCK_OUT
            }]
        }
    })


def get_error_response(*args, **kwargs):
    return mocked_response(
        status_code=HTTPStatus.OK,
        json_data={
            'success': False,
            'errors': [],
            'message': 'error',
            'code': 'code'
        },
    )


def get_new_stamp_response(*args, **kwargs):
    return mocked_response(
        status_code=HTTPStatus.OK,
        json_data={
            'success': True,
            'response': {
                'stampedAt': '2020/01/01 00:00:00',
                'type': CLOCK_IN
            }
        },
    )


def get_reissued_token_response(*args, **kwargs):
    return mocked_response(
        status_code=HTTPStatus.OK,
        json_data={
            'success': True,
            'response': {
                'token': dummy_token,
                'expired_at': '2020/02/01 00:00:00'
            }
        },
    )


def get_not_found_response(*args, **kwargs):
    return mocked_response(status_code=HTTPStatus.NOT_FOUND, json_data={})


def mocked_response(json_data: dict = {}, status_code: int = HTTPStatus.OK):
    class MockedResponse:
        def __init__(self, json_data: dict = {}, status_code: int = HTTPStatus.OK):
            self.status_code = status_code
            self.json_data = json_data

        def json(self):
            return self.json_data

        @property
        def ok(self):
            return self.status_code == HTTPStatus.OK

    return MockedResponse(json_data, status_code)


def test_annotate_stamp_type():
    assert annotate_stamp_type(CLOCK_IN) == '勤務を開始:office:'
    assert annotate_stamp_type(CLOCK_OUT) == '勤務を終了:house:'
    assert annotate_stamp_type(STRAIGHT_TO) == '直行:train:'
    assert annotate_stamp_type(LEAVE_DIRECTLY) == '直帰:beer:'
    assert annotate_stamp_type(BREAK) == '休憩を開始:coffee:'
    assert annotate_stamp_type(RESTART) == '休憩を終了:computer:'


class StampTest(TestCase):
    def test_stamped_at(self):
        raise AssertionError
        stamp = Stamp(stamped_at='2020/01/01 00:00:00', type=CLOCK_IN)
        self.assertEqual(stamp.stamped_at, datetime(2020, 1, 1))


class NewStampResponseTest(TestCase):
    def test_stamped_at(self):
        response = NewStampResponse(**{'stampedAt': '2020/01/01 00:00:00', 'type': BREAK})
        self.assertEqual(response.stamped_at, datetime(2020, 1, 1))


class ReissuedTokenResponseTest(TestCase):
    def test_expired_at(self):
        response = ReissuedTokenResponse(expired_at='2020/01/01 00:00:00', token=dummy_token)
        self.assertEqual(response.expired_at, datetime(2020, 1, 1))


class AkashiRequestClientTest(TestCase):
    akashi: AkashiRequestClient

    @classmethod
    def setUpClass(cls):
        cls.akashi = AkashiRequestClient(dummy_token)

    @mock.patch('app.akashi.AkashiRequestClient.fetch_stamps', lambda *x: FetchedStampResponse(count=0, stamps=[]))
    def test_fetch_last_stamp_case_none(self, *args):
        self.assertIsNone(self.akashi.fetch_last_stamp())

    @mock.patch('requests.Session.request', get_stamp_response)
    def test_fetch_last_stamp_case_clocked_in(self):
        expected = Stamp(stamped_at='2020/01/01 18:00:00', type=CLOCK_OUT)
        self.assertEqual(self.akashi.fetch_last_stamp(), expected)

    @mock.patch('requests.Session.request', get_stamp_response)
    def test_fetch_stamps(self):
        expected = [
            Stamp(stamped_at='2020/01/01 09:00:00', type=CLOCK_IN),
            Stamp(stamped_at='2020/01/01 18:00:00', type=CLOCK_OUT)
        ]
        res = self.akashi.fetch_stamps(date(2020, 1, 1), date(2020, 1, 1))
        self.assertEqual(res.stamps, expected)

    @mock.patch('requests.Session.request', get_error_response)
    def test_request_case_error(self):
        with self.assertRaises(APIError):
            self.akashi.fetch_last_stamp()

    @mock.patch('requests.Session.request', get_new_stamp_response)
    def test_new_stamp(self):
        stamp = self.akashi.stamp(CLOCK_IN)
        self.assertEqual(stamp.type, CLOCK_IN)

    @mock.patch('requests.Session.request', get_reissued_token_response)
    def test_reissue_token(self):
        reissued_token_response = self.akashi.reissue_token()
        self.assertIsInstance(reissued_token_response.expired_at, datetime)

    @mock.patch('requests.Session.request', get_not_found_response)
    def test_not_found(self):
        with self.assertRaises(RequestFailedError):
            self.akashi.fetch_last_stamp()
