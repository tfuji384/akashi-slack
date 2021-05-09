import json
from http import HTTPStatus
from unittest import TestCase
from unittest.mock import patch

from fastapi import Request
from fastapi.testclient import TestClient

from app import api, get_db, verify_signature
from app.akashi import CLOCK_IN, CLOCK_OUT, NewStampResponse, Stamp
from app.crud import fetch, fetch_all
from app.settings import settings
from tests.factories import UserTokenFactory
from tests.helpers import Base, engine, session
from tests.test_akashi import dummy_token, get_error_response, mocked_response


async def override_verification(request: Request = None):
    return True


def get_test_db():
    try:
        return session
    except:
        session.close()


client = TestClient(api)
api.dependency_overrides[verify_signature] = override_verification
api.dependency_overrides[get_db] = get_test_db


def test_root():
    res = client.get('/')
    assert res.status_code == 200


class SlashTest(TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)

    @patch('app.slack.dialog_open', lambda trigger_id, dialog: True)
    def test_slash_case_token_unregistered(self):
        res = client.post('/slash', data={'user_id': '', 'trigger_id': ''})
        assert res.status_code == HTTPStatus.OK
        assert res.text == ''

    @patch('app.akashi.AkashiRequestClient.fetch_last_stamp',
           lambda *args: Stamp(type=CLOCK_OUT, stamped_at='2020/01/01 19:00:00'))
    def test_slash_case_already_clocked_out(self):
        instance = UserTokenFactory.create()
        res = client.post('/slash', data={'user_id': instance.user_id, 'trigger_id': ''})
        assert res.text == 'すでに勤務を終了しています。'

    @patch('app.joined', lambda *x, **y: False)
    def test_not_joined(self):
        res = client.post('/slash', data={'user_id': '', 'trigger_id': ''})
        assert res.text, ':warning:エラーが発生しました\n'\
            f'- 環境変数の`SLACK_CHANNEL_ID`を確認してください（現在の値：{settings.SLACK_CHANNEL_ID}）\n'\
            '- private-channelには通知できません\n'\
            '- 打刻の通知が不要な場合は環境変数の`SLACK_CHANNEL_ID`を削除してください\n'\
            '- SlackAppのOAuth scopeに`channels:join`が追加されていることを確認してください'


class ActionsTest(TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)

    @patch('app.slack.api_call', lambda *x, **y: True)
    def test_register_valid_api_token(self):
        user_id = 'xxxxxxxx'
        data = {
            'payload': json.dumps({
                'user': {
                    'id': user_id
                },
                'callback_id': 'api_token',
                'submission': {
                    'api_token': dummy_token
                }
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, '')
        self.assertEqual(len(fetch_all(get_test_db())), 1)

    @patch('app.slack.api_call', lambda *x, **y: True)
    def test_update_valid_api_token(self):
        instance = UserTokenFactory()
        data = {
            'payload': json.dumps({
                'user': {
                    'id': instance.user_id
                },
                'callback_id': 'api_token',
                'submission': {
                    'api_token': dummy_token
                }
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, '')
        self.assertEqual(fetch(get_test_db(), instance.user_id).id, instance.id)

    @patch('app.slack.api_call', lambda *x, **y: True)
    def test_register_invalid_api_token(self):
        user_id = 'xxxxxxxx'
        data = {
            'payload': json.dumps({
                'user': {
                    'id': user_id
                },
                'callback_id': 'api_token',
                'submission': {
                    'api_token': f'{dummy_token}1'
                }
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, '')
        self.assertIsNone(fetch(get_test_db(), user_id=user_id))

    @patch('app.slack.api_call', lambda *x, **y: True)
    @patch(
        'app.akashi.AkashiRequestClient.stamp',
        lambda *x, **y: NewStampResponse(stampedAt='2021/05/08 00:00:00', type=CLOCK_IN),
    )
    def test_stamp(self):
        user_tokens = UserTokenFactory()
        data = {
            'payload': json.dumps({
                'callback_id': 'stamp',
                'user': {
                    'id': user_tokens.user_id
                },
                'actions': [{
                    'value': CLOCK_IN
                }]
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, '勤務を開始:office:しました（時刻：2021-05-08 00:00:00）')

    @patch('app.akashi.AkashiRequestClient.request_', get_error_response)
    def test_stamp_failed(self):
        user_tokens = UserTokenFactory()
        data = {
            'payload': json.dumps({
                'callback_id': 'stamp',
                'user': {
                    'id': user_tokens.user_id
                },
                'actions': [{
                    'value': CLOCK_IN
                }]
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, 'APIトークンを確認してください')

    @patch('app.akashi.AkashiRequestClient.request_',
           lambda *x, **y: mocked_response({}, status_code=HTTPStatus.NOT_FOUND))
    def test_stamp_akashi_api_server_error(self):
        user_tokens = UserTokenFactory()
        data = {
            'payload': json.dumps({
                'callback_id': 'stamp',
                'user': {
                    'id': user_tokens.user_id
                },
                'actions': [{
                    'value': CLOCK_IN
                }]
            })
        }
        res = client.post('/actions', data=data)
        self.assertEqual(res.text, 'エラーが発生しました')
