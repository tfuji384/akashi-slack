import json
import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from slack_sdk import WebClient
from slack_sdk.models.dialogs import DialogBuilder, DialogTextField
from slack_sdk.signature import SignatureVerifier
from sqlalchemy.orm import Session

from app.akashi import AkashiRequestClient, APIError, annotate_stamp_type
from app.buttons import AlreadyClockedOutException, get_buttons
from app.crud import fetch, update_or_create
from app.db import SessionLocal
from app.settings import settings

api = FastAPI(docs_url=None, redoc_url=None)
logger = logging.getLogger(__name__)
slack = WebClient(settings.SLACK_BOT_TOKEN)


async def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def verify_signature(request: Request) -> bool:
    verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
    if verifier.is_valid_request(await request.body(), dict(request.headers)):
        return True
    raise HTTPException(HTTPStatus.FORBIDDEN)


def joined() -> bool:
    channel = settings.SLACK_CHANNEL_ID
    if channel:
        try:
            slack.conversations_join(channel=channel)
            return True
        except Exception as e:
            logger.error(e, exc_info=True)
            return False
    return True


@api.post('/slash', status_code=HTTPStatus.OK, dependencies=[Depends(verify_signature)])
async def slash(request: Request, db: Session = Depends(get_db)):
    if not joined():
        message = ':warning:エラーが発生しました\n'\
            f'- 環境変数の`SLACK_CHANNEL_ID`を確認してください（現在の値：{settings.SLACK_CHANNEL_ID}）\n'\
            '- private-channelには通知できません\n'\
            '- 打刻の通知が不要な場合は環境変数の`SLACK_CHANNEL_ID`を削除してください\n'\
            '- SlackAppのOAuth scopeに`channels:join`が追加されていることを確認してください'
        return Response(message)
    form = await request.form()
    user_id = form['user_id']
    trigger_id = form['trigger_id']
    try:
        user_token = fetch(db, user_id=user_id)
        akashi = AkashiRequestClient(user_token.token)
        last_stamp = akashi.fetch_last_stamp()
        return {
            'attachments': [{
                'attachment_type': 'stamp',
                'callback_id': 'stamp',
                'color': '#3AA3E3',
                'actions': get_buttons(last_stamp)
            }]
        }
    except AlreadyClockedOutException:
        return Response('すでに勤務を終了しています。')
    except:
        dialog = DialogBuilder()
        dialog.callback_id('api_token').title('APIトークンを登録する').submit_label('Submit').state('Limo').text_area(
            name='api_coken', label='APIトークンを入力してください', hint='https://atnd.ak4.jp/mypage/tokens から発行できます')
        slack.dialog_open(
            dialog=dialog.to_dict(),
            trigger_id=trigger_id,
        )
        return Response()


@api.post('/actions', status_code=HTTPStatus.OK, dependencies=[Depends(verify_signature)])
async def actions(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    payload = json.loads(form['payload'])
    callback_id = payload['callback_id']
    user_id = payload['user']['id']

    if callback_id == 'api_token':
        try:
            api_token = payload['submission']['api_token'].strip()
            UUID(api_token)
            update_or_create(db=db, user_id=user_id, token=api_token)
            slack.chat_postMessage(channel=user_id, text='APIトークンを登録しました')
        except ValueError:
            # APIトークンがUUID形式でなかった場合
            slack.chat_postMessage(channel=user_id, text='APIトークンが（おそらく）正しくありません')
            return Response()
        except Exception as e:
            logger.error(e, exc_info=True)
        return Response()
    elif callback_id == 'stamp':
        user_token = fetch(db, user_id=user_id)
        akashi = AkashiRequestClient(user_token=user_token.token)
        try:
            stamp = akashi.stamp(payload['actions'][0]['value'])
            slack.chat_postMessage(
                channel=settings.SLACK_CHANNEL_ID,
                text=f'<@{user_id}>さんが{annotate_stamp_type(stamp.type)}しました',
            )
        except APIError as e:
            logger.error(e, exc_info=True)
            return Response('APIトークンを確認してください')
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response('エラーが発生しました')
        else:
            return Response(f'{annotate_stamp_type(stamp.type)}しました（時刻：{stamp.stamped_at}）')


@api.get('/', status_code=HTTPStatus.OK)
async def root(req: Request):
    return {}
