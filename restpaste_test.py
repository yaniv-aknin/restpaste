#!/usr/bin/env python

from httplib import CREATED, OK, NOT_FOUND, NO_CONTENT
import unittest

from werkzeug.contrib.cache import SimpleCache

import restpaste

class RestPasteTestCase(unittest.TestCase):

    def setUp(self):
        restpaste.app.config['TESTING_CACHE'] = SimpleCache()
        self.app = restpaste.app.test_client()

    def assertHeaders(self, rv, expected):
        for header_tuple in expected:
            self.assertIn(header_tuple, rv.headers.items())

    def test_index(self):
        plain = self.app.get('/')
        self.assertIn('@aknin', plain.data)
        self.assertNotIn('html', plain.data)
        self.assertHeaders(plain, restpaste.PLAIN)
        html = self.app.get('/', headers=(('Accept', 'text/html'),))
        self.assertIn('text/html', html.headers['Content-Type'])
        self.assertIn('html', html.data)

    def test_get_404(self):
        rv = self.app.get('/foo')
        self.assertEquals(rv.status_code, NOT_FOUND)
        self.assertHeaders(rv, restpaste.PLAIN)

    def test_get(self):
        self.app.put('/foo', data='bar')
        rv = self.app.get('/foo')
        self.assertEquals(rv.status_code, OK)
        self.assertEquals(rv.data, 'bar')
        self.assertHeaders(rv, restpaste.OCTET_STREAM)

    def test_put(self):
        def non_idempotent(expected_status, data):
            rv = self.app.put('/foo', data=data)
            self.assertEquals(rv.status_code, expected_status)
            self.assertEquals(rv.data, data)
            self.assertHeaders(rv, restpaste.OCTET_STREAM)
        non_idempotent(CREATED, 'bar') # first request creates
        non_idempotent(OK, 'baz') # second request updates

    def test_post(self):
        rv = self.app.post('/foo', data='bar')
        self.assertEquals(rv.status_code, CREATED)
        self.assertEquals(rv.data, 'bar')
        self.assertHeaders(rv, restpaste.OCTET_STREAM)
        self.assertIn('Location', rv.headers)
        new_loc = rv.headers['Location']
        rv = self.app.get(new_loc)
        self.assertEquals(rv.data, 'bar')

    def test_delete(self):
        self.app.put('/foo', data='bar')
        rv = self.app.delete('/foo')
        self.assertEquals(rv.status_code, NO_CONTENT)
        missing = self.app.get('/foo')
        self.assertEquals(missing.status_code, NOT_FOUND)

    def test_global_delete(self):
        self.app.put('/foo', data='bar')
        rv = self.app.delete('/')
        self.assertEquals(rv.status_code, OK)
        missing = self.app.get('/foo')
        self.assertEquals(missing.status_code, NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
