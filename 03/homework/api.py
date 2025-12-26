#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import logging
import hashlib
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if not isinstance(value, str):
            raise ValueError("must be a string")
        return value


class ArgumentsField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if not isinstance(value, dict):
            raise ValueError("must be a dict")
        return value


class EmailField(CharField):
    def clean(self, value):
        value = super().clean(value)
        if value and "@" not in value:
            raise ValueError("must contain @")
        return value


class PhoneField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if isinstance(value, bool):
            raise ValueError("must be a string or int")
        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str):
            raise ValueError("must be a string or int")
        if value:
            if not value.isdigit():
                raise ValueError("must be digits")
            if len(value) != 11:
                raise ValueError("must be length 11")
            if not value.startswith("7"):
                raise ValueError("must start with 7")
        return value


class DateField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if not isinstance(value, str):
            raise ValueError("must be a string date")
        try:
            return datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("invalid date format")


class BirthDayField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if not isinstance(value, str):
            raise ValueError("must be a string date")
        try:
            dt = datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("invalid date format")
        today = datetime.datetime.today()
        try:
            limit = dt.replace(year=dt.year + 70)
        except ValueError:
            limit = dt + datetime.timedelta(days=70 * 365)
        if limit < today:
            raise ValueError("too old")
        return dt


class GenderField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("must be int")
        if value not in GENDERS:
            raise ValueError("invalid gender")
        return value


class ClientIDsField(object):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.name = None

    def clean(self, value):
        if not isinstance(value, list):
            raise ValueError("must be a list")
        if not value:
            raise ValueError("must be non-empty")
        for item in value:
            if isinstance(item, bool) or not isinstance(item, int):
                raise ValueError("must be int list")
        return value


class RequestMeta(type):
    def __new__(mcls, name, bases, namespace):
        fields = {}
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, (CharField, ArgumentsField, EmailField, PhoneField,
                                       DateField, BirthDayField, GenderField, ClientIDsField)):
                attr_value.name = attr_name
                fields[attr_name] = attr_value
        namespace["_fields"] = fields
        return super().__new__(mcls, name, bases, namespace)


class RequestBase(object, metaclass=RequestMeta):

    def __init__(self, data):
        self._data = data or {}
        self._errors = []
        self._validate()

    def _validate(self):
        for name, field in self._fields.items():
            if name not in self._data:
                if field.required:
                    self._errors.append("%s is required" % name)
                else:
                    setattr(self, name, None)
                continue
            value = self._data.get(name)
            if value is None:
                if field.nullable:
                    setattr(self, name, None)
                    continue
                self._errors.append("%s cannot be null" % name)
                continue
            if value == "" and field.nullable:
                setattr(self, name, value)
                continue
            try:
                cleaned = field.clean(value)
            except ValueError as exc:
                self._errors.append("%s %s" % (name, exc))
                continue
            setattr(self, name, cleaned)

    @property
    def is_valid(self):
        return not self._errors

    @property
    def errors(self):
        return self._errors


class ClientsInterestsRequest(RequestBase):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(RequestBase):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(RequestBase):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=False)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        account = request.account or ""
        digest = hashlib.sha512((account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    body = request.get("body") or {}
    method_request = MethodRequest(body)
    if not method_request.is_valid:
        return ", ".join(method_request.errors), INVALID_REQUEST

    if not check_auth(method_request):
        return ERRORS[FORBIDDEN], FORBIDDEN

    if method_request.method == "online_score":
        score_request = OnlineScoreRequest(method_request.arguments)
        if not score_request.is_valid:
            return ", ".join(score_request.errors), INVALID_REQUEST

        pairs = (
            (score_request.phone, score_request.email),
            (score_request.first_name, score_request.last_name),
            (score_request.gender, score_request.birthday),
        )
        if not any(all(v is not None and v != "" for v in pair) for pair in pairs):
            return "Not enough arguments", INVALID_REQUEST

        ctx["has"] = [k for k, v in method_request.arguments.items() if v is not None and v != ""]
        if method_request.is_admin:
            return {"score": 42}, OK
        from scoring import get_score
        score = get_score(store, score_request.phone, score_request.email,
                          score_request.birthday, score_request.gender,
                          score_request.first_name, score_request.last_name)
        return {"score": score}, OK

    if method_request.method == "clients_interests":
        interests_request = ClientsInterestsRequest(method_request.arguments)
        if not interests_request.is_valid:
            return ", ".join(interests_request.errors), INVALID_REQUEST
        ctx["nclients"] = len(interests_request.client_ids)
        from scoring import get_interests
        response = {str(cid): get_interests(store, cid) for cid in interests_request.client_ids}
        return response, OK

    return ERRORS[NOT_FOUND], NOT_FOUND


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except (ValueError, json.JSONDecodeError, KeyError, OSError):
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
