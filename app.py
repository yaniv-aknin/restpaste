from httplib import CREATED, OK, NOT_FOUND, NO_CONTENT
from functools import wraps
from uuid import uuid4
import os

from flask import Flask, request, g
from flask.views import MethodView
from markdown import markdown
import bmemcached

app = Flask(__name__)

def build_memcached_client():
    return bmemcached.Client(
        servers=[os.environ.get('MEMCACHIER_SERVERS', 'localhost')],
        username=os.environ.get('MEMCACHIER_USERNAME', ''),
        password=os.environ.get('MEMCACHIER_PASSWORD', ''),
    )

# this class casts keys to str because bmemcached chokes on unicode
class Store(object):
    def __init__(self):
        self.client = build_memcached_client()
    def __getitem__(self, name):
        return self.client.get(str(name))
    def __setitem__(self, name, value):
        self.client.set(str(name), value)
    def __delitem__(self, name):
        self.client.delete(str(name))
    def __contains__(self, name):
        return self.client.get(str(name)) is not None

with open('README.md') as handle:
    PLAIN_INDEX=handle.read()
MARKDOWN_INDEX=markdown(PLAIN_INDEX)

PLAIN=(('Content-Type', 'text/plain'),)
OCTET_STREAM=(('Content-Type', 'application/octet-stream'),)

@app.before_request
def before_request():
    g.store = Store()

@app.route('/')
def index():
    if request.method.lower() == 'DELETE':
        build_memcached_client().flush_all()
        return '', NO_CONTENT
    if 'html' in request.headers.get('Accept', '*/*'):
        return MARKDOWN_INDEX, OK
    return PLAIN_INDEX, OK, PLAIN

class Service(MethodView):
    def key_or_404(func):
        @wraps(func)
        def inner(self, key):
            if key not in g.store:
                return 'no such key', NOT_FOUND, PLAIN
            return func(self, key)
        return inner
    @key_or_404
    def get(self, key):
        return g.store[key], OK, OCTET_STREAM
    def put(self, key):
        existed = key in g.store
        g.store[key] = request.data
        return g.store[key], OK if existed else CREATED, OCTET_STREAM
    @key_or_404
    def delete(self, key):
        del g.store[key]
        return '', NO_CONTENT
    def post(self, key):
        key = "/".join((key, uuid4().hex))
        g.store[key] = request.data
        return g.store[key], CREATED, dict(OCTET_STREAM, Location=key)
app.add_url_rule('/<path:key>', view_func=Service.as_view('service'))

if __name__ == '__main__':
    app.run(debug=True)
