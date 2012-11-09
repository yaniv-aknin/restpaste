from httplib import CREATED, OK, NOT_FOUND, NO_CONTENT
from functools import wraps
from uuid import uuid4

from flask import Flask, request
from flask.views import MethodView
from markdown import markdown

app = Flask(__name__)

class Store(object):
    def __init__(self):
        self.data = {}
    def __getitem__(self, name):
        return self.data[name]
    def __setitem__(self, name, value):
        self.data[name] = value
    def __delitem__(self, name):
        del self.data[name]
    def __contains__(self, name):
        return name in self.data
store = Store()

with open('README.md') as handle:
    PLAIN_INDEX=handle.read()
MARKDOWN_INDEX=markdown(PLAIN_INDEX)

PLAIN=(('Content-Type', 'text/plain'),)
OCTET_STREAM=(('Content-Type', 'application/octet-stream'),)

@app.route('/')
def index():
    if 'html' in request.headers.get('Accept', '*/*'):
        return MARKDOWN_INDEX, OK
    return PLAIN_INDEX, OK, PLAIN

class Service(MethodView):
    def key_or_404(func):
        @wraps(func)
        def inner(self, key):
            if key not in store:
                return 'no such key', NOT_FOUND, PLAIN
            return func(self, key)
        return inner
    @key_or_404
    def get(self, key):
        return store[key], OK, OCTET_STREAM
    def put(self, key):
        existed = key in store
        store[key] = request.data
        return store[key], OK if existed else CREATED, OCTET_STREAM
    @key_or_404
    def delete(self, key):
        del store[key]
        return '', NO_CONTENT
    def post(self, key):
        key = "/".join((key, uuid4().hex))
        store[key] = request.data
        return store[key], CREATED, dict(OCTET_STREAM, Location=key)
app.add_url_rule('/<path:key>', view_func=Service.as_view('service'))

if __name__ == '__main__':
    app.run(debug=True)
