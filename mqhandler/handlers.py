# -*- coding: utf-8 -*-

import sys
import logging
import threading
from datetime import datetime

import pika
from pika import credentials

logger = logging.getLogger(__name__)


class RabbitHandler(logging.Handler):
    """
    handler that send log to rabbitmq, using pika.
    """

    def __init__(self, host, port=None, virtual_host=None, username=None, password=None, exchange='log'):
        logging.Handler.__init__(self)
        self.connection_para = dict(host=host)
        if port:
            self.connection_para['port'] = port
        if virtual_host:
            self.connection_para['virtual_host'] = virtual_host
        if username and password:
            self.connection_para['credentials'] = credentials.PlainCredentials(username, password)
        self.exchange = exchange
        self.connection, self.channel = None, None

        # make sure exchange only declared once.
        self.is_exchange_declared = False
        # lock for serializing log sending, because pika is not thread safe.
        self.emit_lock = threading.Lock()
        # init connection.
        self.connect()

    def connect(self):
        """connect to rabbitMq server, using topic exchange"""

        # emit pika to stdout, avoid RecursionError when connecting.
        pika_logger = logging.getLogger('pika')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s'))
        pika_logger.addHandler(handler)
        pika_logger.propagate = False
        pika_logger.setLevel(logging.WARNING)
        # forbidden heartbeat.
        self.connection_para['heartbeat_interval'] = 0
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(**self.connection_para))
        self.channel = self.connection.channel()
        sys.stdout.write('%s - stdout - [mq] Connect success.\n' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not self.is_exchange_declared:
            self.channel.exchange_declare(exchange=self.exchange, type='topic', durable=True, auto_delete=False)
            sys.stdout.write('%s - stdout - [mq] Declare exchange success.\n' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.is_exchange_declared = True

    def emit(self, record):
        self.emit_lock.acquire()
        try:
            if not self.connection or not self.channel:
                self.connect()
            routing_key = "{name}.{level}".format(name=record.name, level=record.levelname)
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=routing_key,
                                       body=self.format(record),
                                       properties=pika.BasicProperties(
                                           delivery_mode=2
                                       ))

        except Exception:
            # for the sake of reconnect
            self.channel, self.connection = None, None
            self.handleError(record)
        finally:
            self.emit_lock.release()

    def close(self):
        """
        clear when closing
        """
        self.acquire()
        try:
            logging.Handler.close(self)
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            sys.stdout.write('%s - stdout - [mq] Clean up success.\n' % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        finally:
            self.release()
