#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import email.utils
import mimetypes
import os
import socket
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Tuple

SERVER_NAME = "simple-httpd"
MAX_HEADER_SIZE = 8192
READ_BUFFER = 64 * 1024
READ_TIMEOUT = 5.0
DEBUG = False

STATUS_MESSAGES = {
    200: "OK",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
}

CONTENT_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".swf": "application/x-shockwave-flash",
}


def guess_content_type(path: Path) -> str:
    content_type = CONTENT_TYPES.get(path.suffix.lower())
    if content_type:
        return content_type
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def debug(message: str) -> None:
    if DEBUG:
        print(f"[debug] {message}", flush=True)


def read_request(conn: socket.socket) -> Optional[bytes]:
    data = b""
    previous_timeout = conn.gettimeout()
    conn.settimeout(READ_TIMEOUT)
    try:
        while b"\r\n\r\n" not in data:
            try:
                chunk = conn.recv(READ_BUFFER)
            except socket.timeout:
                debug("read_request: timeout")
                return None
            if not chunk:
                break
            data += chunk
            if len(data) > MAX_HEADER_SIZE:
                break
    finally:
        conn.settimeout(previous_timeout)
    debug(f"read_request: {len(data)} bytes")
    return data or None


def parse_request(data: bytes) -> Optional[Tuple[str, str, str]]:
    try:
        header_part = data.split(b"\r\n\r\n", 1)[0]
        lines = header_part.decode("iso-8859-1").split("\r\n")
        if not lines:
            return None
        parts = lines[0].split()
        if len(parts) != 3:
            return None
        debug(f"parse_request: {parts[0]} {parts[1]} {parts[2]}")
        return parts[0], parts[1], parts[2]
    except UnicodeDecodeError:
        return None


def resolve_path(doc_root: Path, url_path: str) -> Tuple[Optional[Path], int]:
    path = url_path.split("?", 1)[0]
    wants_dir = path.endswith("/")
    unquoted = urllib.parse.unquote(path)
    rel_path = unquoted.lstrip("/")
    target = (doc_root / rel_path).resolve()
    debug(f"resolve_path: url={url_path} rel={rel_path} target={target}")
    try:
        target.relative_to(doc_root)
    except ValueError:
        debug("resolve_path: forbidden (path traversal)")
        return None, 403

    if target.is_dir():
        if not wants_dir and rel_path:
            return None, 403
        index = target / "index.html"
        if index.exists() and index.is_file():
            debug(f"resolve_path: directory index {index}")
            return index, 200
        debug("resolve_path: index not found")
        return None, 404

    if wants_dir:
        debug("resolve_path: file requested with trailing slash")
        return None, 404

    if not target.exists():
        debug("resolve_path: not found")
        return None, 404
    if not target.is_file():
        debug("resolve_path: forbidden (not a file)")
        return None, 403
    return target, 200


def build_headers(code: int, content_length: int, content_type: Optional[str]) -> bytes:
    lines = [
        f"HTTP/1.1 {code} {STATUS_MESSAGES.get(code, '')}",
        f"Date: {email.utils.formatdate(usegmt=True)}",
        f"Server: {SERVER_NAME}",
        "Connection: close",
        f"Content-Length: {content_length}",
    ]
    if content_type:
        lines.append(f"Content-Type: {content_type}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1")


def handle_client(conn: socket.socket, doc_root: Path) -> None:
    try:
        data = read_request(conn)
        if not data:
            debug("handle_client: empty request")
            return
        parsed = parse_request(data)
        if not parsed:
            debug("handle_client: bad request")
            headers = build_headers(400, 0, "text/plain")
            conn.sendall(headers)
            return
        method, raw_path, _ = parsed

        if method not in ("GET", "HEAD"):
            debug(f"handle_client: method not allowed {method}")
            headers = build_headers(405, 0, "text/plain")
            conn.sendall(headers)
            return

        file_path, status = resolve_path(doc_root, raw_path)
        if status != 200 or file_path is None:
            debug(f"handle_client: resolve status {status}")
            headers = build_headers(status, 0, "text/plain")
            conn.sendall(headers)
            return

        content_type = guess_content_type(file_path)
        content_length = file_path.stat().st_size
        debug(f"handle_client: 200 {file_path} {content_length} bytes")
        headers = build_headers(200, content_length, content_type)
        conn.sendall(headers)
        if method == "GET":
            with file_path.open("rb") as file_obj:
                while True:
                    chunk = file_obj.read(READ_BUFFER)
                    if not chunk:
                        break
                    conn.sendall(chunk)
    except Exception as exc:
        debug(f"handle_client: exception {exc}")
    finally:
        conn.close()


def serve(host: str, port: int, doc_root: Path, workers: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    print(f"Serving HTTP on {host} port {port} (http://{host}:{port}/) ...")
    debug(f"serve: doc_root={doc_root}, workers={workers}")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        while True:
            try:
                conn, addr = sock.accept()
                debug(f"serve: accepted {addr}")
                executor.submit(handle_client, conn, doc_root)
            except Exception as exc:
                debug(f"serve: exception {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--document-root", required=True)
    parser.add_argument("-p", "--port", type=int, default=8080)
    parser.add_argument("-a", "--address", default="0.0.0.0")
    parser.add_argument("-w", "--workers", type=int, default=os.cpu_count() or 4)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    print("Starting server...")
    global DEBUG
    DEBUG = args.debug
    doc_root = Path(args.document_root).resolve()
    if not doc_root.exists() or not doc_root.is_dir():
        raise SystemExit(f"Invalid document root: {doc_root}")

    serve(args.address, args.port, doc_root, args.workers)


if __name__ == "__main__":
    main()
