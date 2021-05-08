from typing import Optional

from app.akashi import (BREAK, CLOCK_IN, CLOCK_OUT, LEAVE_DIRECTLY, RESTART,
                        STRAIGHT_TO, Stamp, annotate_stamp_type)

PRIMARY = 'primary'
DANGER = 'danger'
DEFAULT = 'default'
BUTTON = 'button'

clock_in = dict(text=annotate_stamp_type(CLOCK_IN), name='clock_in', value=CLOCK_IN, style='primary', type=BUTTON)
clock_out = dict(
    text=annotate_stamp_type(CLOCK_OUT),
    confirm=dict(dismiss_text='いいえ', ok_text='はい', text='本当に勤務を終了しますか？', title='確認'),
    name='clock_in',
    value=CLOCK_OUT,
    style='danger',
    type=BUTTON,
)
break_ = dict(text=annotate_stamp_type(BREAK), name='break', value=BREAK, style=DEFAULT, type=BUTTON)
restart = dict(text=annotate_stamp_type(RESTART), name='restart', value=RESTART, style=DEFAULT, type=BUTTON)
leave_directry = dict(text=annotate_stamp_type(LEAVE_DIRECTLY),
                      confirm=dict(dismiss_text='いいえ', ok_text='はい', text='本当に勤務を終了しますか？', title='確認'),
                      name='leave_directry',
                      value=LEAVE_DIRECTLY,
                      style=DANGER,
                      type=BUTTON)
straight_to = dict(text=annotate_stamp_type(STRAIGHT_TO),
                   name='straight_to',
                   value=STRAIGHT_TO,
                   style=DEFAULT,
                   type=BUTTON)


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
