from typing import Optional

from app.akashi import (BREAK, CLOCK_IN, CLOCK_OUT, LEAVE_DIRECTLY, RESTART, STRAIGHT_TO, Stamp, annotate_stamp_type)
from slack_sdk.models.attachments import ActionButton, ConfirmObject

PRIMARY = 'primary'
DANGER = 'danger'
BUTTON = 'button'


def get_button(_type: int, style: Optional[str] = PRIMARY, confirm: Optional[ConfirmObject] = None) -> dict:
    text = annotate_stamp_type(_type)
    return ActionButton(text=text, name=text, value=str(_type), style=style, confirm=confirm).to_dict()


confirm = ConfirmObject(title='確認', deny='いいえ', confirm='はい', text='本当に勤務を終了しますか？')

clock_in = get_button(_type=CLOCK_IN)
clock_out = get_button(_type=CLOCK_OUT, style=DANGER, confirm=confirm)
break_ = get_button(_type=BREAK)
restart = get_button(_type=RESTART)
leave_directry = get_button(_type=LEAVE_DIRECTLY, style=DANGER, confirm=confirm)
straight_to = get_button(_type=STRAIGHT_TO)


class AlreadyClockedOutException(Exception):
    pass


def get_buttons(last_stamp: Optional[Stamp] = None):
    # 打刻がない場合
    if not last_stamp:
        return [clock_in, straight_to]
    stamp_type = last_stamp.type
    # 最後の打刻が休憩の場合
    if stamp_type == BREAK:
        return [restart]
    # すでに勤務を終了
    if stamp_type in [CLOCK_OUT, LEAVE_DIRECTLY]:
        raise AlreadyClockedOutException()
    # それ以外
    return [break_, leave_directry, clock_out]
