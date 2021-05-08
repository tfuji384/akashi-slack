import logging
from datetime import datetime, timedelta

from app.akashi import AkashiRequestClient, APIError, RequestFailedError
from app.crud import delete, fetch_by_expires_at, update
from app.db import session

logger = logging.getLogger(__name__)


def main():
    """
    トークンが期限切れになる前に自動で再発行するスクリプト
    新規で追加したトークンは有効期限がわからないので追加の次のタイミングの実行で再発行の対象にする
    """
    update_count = 0
    delete_count = 0
    error_count = 0

    instances = fetch_by_expires_at(session, datetime.today() + timedelta(days=2))
    for instance in instances:
        akashi = AkashiRequestClient(instance.token)
        try:
            response = akashi.reissue_token()
            update(session, instance, response.token, response.expired_at)
            update_count += 1
        except (APIError, RequestFailedError) as e:
            logger.error(e)
            delete_count += 1
            delete(session, instance)
    print(f'更新バッチの実行が完了しました（対象：{len(instances):,}件）')
    print(f'更新：{update_count:,}件')
    print(f'削除：{delete_count:,}件')
    print(f'エラー：{error_count:,}件')


if __name__ == '__main__':
    main()
