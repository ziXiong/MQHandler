RabbitHandler
=============
Log handler that emit log to rabbit mq server.


Examples
========

### how to set up an rabbithandler

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mqhandler': {
            'level': 'DEBUG',
            'class': 'mqhandler.RabbitHandler',
            'formatter': 'verbose',
            'host': 'localhost',
            'exchange': 'my_log'
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
        },
    },
    'root': {
        'handlers': ['mqhandler'],
        'level': 'DEBUG',
        'propagate': True,
    }
}

from logging.config import dictConfig
dictConfig(LOGGING)
```

Then make log as usual.

### how to consume

RabbitHandler use a topic exchange with a key `{name}.{level}`. This is a common for logging system. You can register a subscriber to consume whatever log you want.  

### 一篇介绍
[python下如何利用RabbitMq广播日志](http://www.z1xiong.me/blog/2016/05/03/building-log-system-with-rabbitmq-and-python.html)
