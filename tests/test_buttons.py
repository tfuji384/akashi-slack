from pytest import raises

from app.akashi import (BREAK, CLOCK_IN, CLOCK_OUT, LEAVE_DIRECTLY, RESTART,
                        STRAIGHT_TO, Stamp)
from app.buttons import (AlreadyClockedOutException, break_, clock_in,
                         clock_out, get_buttons, leave_directry, restart,
                         straight_to)


def test_get_buttons_case_last_stamp_is_none():
    buttons = get_buttons()
    assert buttons == [clock_in, straight_to]


def test_get_buttons_case_last_stamp_is_clock_in():
    buttons = get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=CLOCK_IN))
    assert buttons == [break_, leave_directry, clock_out]


def test_get_buttons_case_last_stamp_is_clock_out():
    with raises(AlreadyClockedOutException):
        get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=CLOCK_OUT))


def test_get_buttons_case_last_stamp_is_leave_directry():
    with raises(AlreadyClockedOutException):
        get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=LEAVE_DIRECTLY))


def test_get_buttons_case_last_stamp_is_restart():
    buttons = get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=RESTART))
    assert buttons == [break_, leave_directry, clock_out]


def test_get_buttons_case_last_stamp_is_straight_to():
    buttons = get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=STRAIGHT_TO))
    assert buttons == [break_, leave_directry, clock_out]


def test_get_buttons_case_last_stamp_is_break():
    buttons = get_buttons(Stamp(stamped_at='2021/01/01 00:00:00', type=BREAK))
    assert buttons == [restart]
