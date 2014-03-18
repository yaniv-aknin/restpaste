#!/usr/bin/env python

from httplib import CREATED, OK, NOT_FOUND, NO_CONTENT
from functools import wraps
from uuid import uuid4
import os

from flask import Flask, request, g
from flask.views import MethodView
from markdown import markdown
from urlobject import URLObject
from werkzeug.contrib.cache import RedisCache

app = Flask(__name__)

@app.before_request
def initialize_cache():
    if 'TESTING_CACHE' in app.config:
        g.cache = app.config['TESTING_CACHE']
        return
    url = URLObject(os.environ['REDISCLOUD_URL'])
    g.cache = RedisCache(
        host = url.hostname,
        port = url.port,
        password = url.password,
    )

with open('README.md') as handle:
    PLAIN_INDEX=handle.read()
MINIMAL_HTML_FMT = ("<!doctype html><html lang=en><head><meta charset=utf-8>"
                    "<title>restpaste</title></head><body>%s</body></html>")
MARKDOWN_INDEX=MINIMAL_HTML_FMT % markdown(PLAIN_INDEX)

PLAIN=(('Content-Type', 'text/plain'),)
OCTET_STREAM=(('Content-Type', 'application/octet-stream'),)

@app.route('/', methods={'GET', 'DELETE'})
def index():
    if request.method.upper() == 'DELETE':
        g.cache.clear()
    if 'html' in request.headers.get('Accept', '*/*'):
        return MARKDOWN_INDEX, OK
    return PLAIN_INDEX, OK, PLAIN

class Service(MethodView):
    def key_or_404(func):
        @wraps(func)
        def inner(self, key):
            value = g.cache.get(key)
            if value is None:
                return 'no such key', NOT_FOUND, PLAIN
            return func(self, key, value)
        return inner
    @key_or_404
    def get(self, key, value):
        return value, OK, OCTET_STREAM
    def put(self, key):
        existed = g.cache.get(key) is not None
        value = request.data
        g.cache.set(key, value)
        return value, OK if existed else CREATED, OCTET_STREAM
    @key_or_404
    def delete(self, key, value):
        g.cache.delete(key)
        return '', NO_CONTENT
    def post(self, key):
        key = "/".join((key, uuid4().hex))
        value = request.data
        g.cache.set(key, value)
        return value, CREATED, dict(OCTET_STREAM, Location=key)
app.add_url_rule('/<path:key>', view_func=Service.as_view('service'))

if __name__ == '__main__':
    app.run(debug=True)
