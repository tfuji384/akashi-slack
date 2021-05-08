from datetime import datetime
from string import ascii_letters
from unittest import TestCase
from uuid import uuid4

from rstr import rstr

from app.crud import (delete, fetch, fetch_all, fetch_by_expires_at,
                      update_or_create)
from tests.factories import UserTokenFactory
from tests.helpers import Base, engine, session


class CRUDTest(TestCase):
    def setUp(self):
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)

    def test_fetch_none(self):
        dummy_user_id = rstr(ascii_letters, 11)
        self.assertIsNone(fetch(session, dummy_user_id))

    def test_fetch(self):
        instance = UserTokenFactory.create()
        fetched = fetch(session, instance.user_id)
        self.assertEqual(instance.id, fetched.id)

    def test_fetch_all(self):
        UserTokenFactory.create()
        self.assertEqual(len(fetch_all(session)), 1)

    def test_delete(self):
        instance = UserTokenFactory.create()
        delete(session, instance)
        self.assertEqual(len(fetch_all(session)), 0)

    def test_update_or_create_case_update(self):
        instance = UserTokenFactory.create()
        updated = update_or_create(session, instance.user_id)
        self.assertEqual(instance.id, updated.id)

    def test_update_or_create_case_create(self):
        update_or_create(session, user_id=rstr(ascii_letters, 11), token=str(uuid4()))
        self.assertEqual(len(fetch_all(session)), 1)

    def test_fetch_by_expires_at(self):
        instance_1 = UserTokenFactory.create()
        instance_2 = UserTokenFactory.create(expires_at=datetime(2020, 12, 31, 23, 59, 59))
        instance_3 = UserTokenFactory.create(expires_at=datetime(2021, 1, 1))
        instances = fetch_by_expires_at(session, datetime(2021, 1, 1))
        self.assertIn(instance_1, instances)
        self.assertIn(instance_2, instances)
        self.assertNotIn(instance_3, instances)
