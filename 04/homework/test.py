import datetime
import hashlib
import json
import unittest

import api
import scoring
from store import Store


def cases(case_list):
    def decorator(func):
        def wrapper(self):
            for item in case_list:
                args = item if isinstance(item, tuple) else (item,)
                with self.subTest(case=item):
                    func(self, *args)

        return wrapper

    return decorator


class DummyCacheStore:
    def __init__(self, cached=None, fail_cache=False):
        self.cached = cached
        self.fail_cache = fail_cache
        self.cached_set = None

    def cache_get(self, key):
        if self.fail_cache:
            raise OSError("cache down")
        return self.cached

    def cache_set(self, key, value, expire):
        if self.fail_cache:
            raise OSError("cache down")
        self.cached_set = (key, value, expire)

    def get(self, key):
        return None


class DummyKVStore:
    def __init__(self, data=None):
        self.data = data or {}

    def get(self, key):
        return self.data.get(key)

    def cache_get(self, key):
        return None

    def cache_set(self, key, value, expire):
        self.data[key] = value


class FlakyClient:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.calls = 0

    def get(self, key):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise OSError("connection error")
        return "ok"

    def set(self, key, value, expire):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise OSError("connection error")
        return True


class TestScoring(unittest.TestCase):
    def test_get_score_uses_cache(self):
        store = DummyCacheStore(cached=5)
        score = scoring.get_score(store, phone="79175002040")
        self.assertEqual(score, 5.0)

    def test_get_score_handles_cache_failure(self):
        store = DummyCacheStore(cached=None, fail_cache=True)
        score = scoring.get_score(store, phone="79175002040", email="a@b.ru")
        self.assertGreater(score, 0)

    def test_get_score_sets_cache(self):
        store = DummyCacheStore()
        score = scoring.get_score(store, phone="79175002040")
        self.assertEqual(score, 1.5)
        self.assertIsNotNone(store.cached_set)

    def test_get_interests_from_store(self):
        interests = json.dumps(["books", "music"])
        store = DummyKVStore({"i:42": interests})
        result = scoring.get_interests(store, "42")
        self.assertEqual(result, ["books", "music"])


class TestStore(unittest.TestCase):
    def test_store_retries(self):
        client = FlakyClient(fail_times=1)

        def factory(timeout):
            return client

        store = Store(factory, retries=2, timeout=1)
        self.assertEqual(store.get("key"), "ok")

    def test_store_raises_after_retries(self):
        client = FlakyClient(fail_times=5)

        def factory(timeout):
            return client

        store = Store(factory, retries=2, timeout=1)
        with self.assertRaises(OSError):
            store.get("key")


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = DummyKVStore()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            msg = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(msg.encode("utf-8")).hexdigest()
        else:
            msg = (request.get("account", "") + request.get("login", "") + api.SALT).encode("utf-8")
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases(
        [
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "sdd",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "admin",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
        ]
    )
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases(
        [
            {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
            {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
            {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
        ]
    )
    def test_invalid_method_request(self, request):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases(
        [
            {"phone": "79175002040", "email": "stupnikov@otus.ru"},
            {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        ]
    )
    def test_ok_score_request(self, arguments):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertIn("score", response)


if __name__ == "__main__":
    unittest.main()
