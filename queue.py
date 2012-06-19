import pika
import json
import conf

class FpQueue(object):
    # XXX: Methods don't work if queue isn't there
    # (e.g. size, delete a second time)

    def __init__(self, queuename):
        self.queuename = queuename
        self.appcb = None
        credentials = pika.PlainCredentials(conf.queueuser, conf.queuepass)
        parameters = pika.ConnectionParameters(host=conf.queuehost, virtual_host=conf.queuevhost, credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=self.queuename, durable=True,
                  exclusive=False, auto_delete=False)

    def put(self, data):
        d = json.dumps(data)
        self.channel.basic_publish(exchange='',
                  routing_key=self.queuename,
                  body=d,
                  properties=pika.BasicProperties(
                      content_type="application/json",
                      delivery_mode=2))

    def clear_queue(self):
        self.channel.queue_delete(queue=self.queuename)

    def size(self):
        status = self.channel.queue_declare(queue=self.queuename, passive=True)
        return status.method.message_count

    def get(self):
        self.channel.basic_qos(prefetch_count=1)
        method_frame, header_frame, body = self.channel.basic_get(queue=self.queuename)
        if method_frame.NAME == 'Basic.GetEmpty':
            return (None, None)
        else:
            data = json.loads(body)
            return (data, method_frame)

    def ack(self, method_frame):
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

