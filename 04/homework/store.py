class InMemoryClient:
    def __init__(self, timeout=2):
        self._data = {}

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value, expire):
        self._data[key] = value
        return True


class Store:
    def __init__(self, client_factory, retries=3, timeout=2):
        self._client_factory = client_factory
        self._retries = retries
        self._timeout = timeout
        self._client = None

    def _connect(self):
        self._client = self._client_factory(timeout=self._timeout)

    def _call(self, method, *args, **kwargs):
        last_exc = None
        for _ in range(self._retries):
            if self._client is None:
                self._connect()
            try:
                fn = getattr(self._client, method)
                return fn(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                self._client = None
        if last_exc:
            raise last_exc
        raise RuntimeError("store call failed without exception")

    def get(self, key):
        return self._call("get", key)

    def cache_get(self, key):
        return self._call("get", key)

    def cache_set(self, key, value, expire):
        return self._call("set", key, value, expire)
