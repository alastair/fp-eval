import pika
import json
class FpQueue(object):

    def __init__(self, queuename):
        self.queuename = queuename
        self.appcb = None
        parameters = pika.ConnectionParameters('localhost')
        self.connection = pika.BlockingConnection(parameters)
        self.channel = connection.channel()

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

    def cb(self, ch, method, properties, body):
        d = json.loads(body)
        if self.appcb:
            self.appcb(d)
            ch.basic_ack(delivery_tag = method.delivery_tag)
        else:
            print "NO CALLBACK TO ACKNOWLEDGE!"

    def size(self):
        pass

    def clear_queue(self):
        print "clearing queue"
        pass

    def consume(self, mycb):
        self.appcb = mycb
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.cb,
                      queue=self.queuename)
        self.channel.start_consuming()

