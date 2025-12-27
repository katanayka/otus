# HTTP Server (Homework 06)

Simple HTTP/1.1 static file server with manual parsing, GET/HEAD support,
directory index handling, and safe path resolution.

## Structure
- `homework/httpd.py` - server implementation
- `homework/httptest` - document root content
- `tests/http-test-suite` - functional tests

## Requirements
- Python 3.10+

## Run server
From the repository root:
```bash
python 06/homework/httpd.py -r 06/homework -p 8080
```

Optional debug output:
```bash
python 06/homework/httpd.py -r 06/homework -p 8080 --debug
```

`-r` must point to a directory that contains the `httptest` folder.
If port 8080 is busy, use another port and update the URLs below.

## Quick checks
```bash
curl -I http://localhost:8080/httptest/dir2/page.html
curl http://localhost:8080/httptest/wikipedia_russia.html
```

## Run tests (http-test-suite)
The suite expects port 80 by default.

Option A: bind to port 80 (may require admin/sudo):
```bash
python 06/homework/httpd.py -r 06/homework -p 80
python 06/tests/http-test-suite/httptest.py
```

Option B: use another port:
1) Change `port` in `06/tests/http-test-suite/httptest.py`
2) Run the server and tests on the same port

## Load test (ab)
Example using Docker on Windows:
```bash
docker run --rm jordi/ab -n 50000 -c 100 -s 120 -r http://host.docker.internal:8080/httptest/dir2/page.html
```
