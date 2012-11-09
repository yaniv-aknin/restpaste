# restpaste

A trivial app to sorta-RESTfully CRUD a shared key:value space with no backing store.

No authentication, no backing store, no bullshit. No guarentee of any kind, your data can and will expire rather rapidly, so use at your own bloody risk.

## Quick and dirty usage

    $ echo 'Hello, world!' | curl -X PUT --data-binary @- restpaste.aknin.name/mykey
    Hello, world!
    $ curl restpaste.aknin.name/mykey
    Hello, world!
    $ 

## Quick and beautiful usage

    $ pip install httpie
    ...
    $ echo 'Hello, world!' | http PUT --body restpaste.aknin.name/mykey
    Hello, world!
    $ http get --body restpaste.aknin.name/mykey
    Hello, world!
    $ 

## What methods are supported?
* `POST` any path to create a new UUID4 subpath (watch the response Location header for the new URL)
* `GET` any path to read the value stored there (or HTTP 404)
* `PUT` any path to update an existing value (or create one if it didn't exist; watch the resulting status code)
* `DELETE` any path to delete the value stored there

## Who wrote it? Can I get the sources?
Why, [`@aknin`](http://twitter.com/#!/aknin) did, and yeah, sure you [can](https://github.com/yaniv-aknin/restpaste).
