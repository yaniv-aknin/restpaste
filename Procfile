web: gunicorn -k gevent -b 0.0.0.0:$PORT restpaste:app
redis: printf 'timeout 0\nlogfile stdout\nloglevel notice\nrequirepass development\n' | redis-server -
