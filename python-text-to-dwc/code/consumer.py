import functools
import pika
import os
import extractor
from typing import NamedTuple
import json
import threading
#import fuzzy_search_python

class Message(NamedTuple):
    ID: str
    Text: str

def publish(response):
    connection = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBIT_MQ_URI")))
    channel = connection.channel()
    out_queue = channel.queue_declare(queue=os.getenv("OUTPUT_QUEUE_PYTHON_DWC"))
    properties = pika.BasicProperties(content_type='text/plain', delivery_mode=pika.DeliveryMode.Persistent)
    channel.basic_publish(exchange='', routing_key=out_queue.method.queue, body=response, properties=properties)
    connection.close()

def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass

def do_work(connection, channel, delivery_tag, body):
    thread_id = threading.get_ident()
    try:
        msg = json.loads(body, object_hook=lambda d: Message(**d))
    except json.JSONDecodeError as err:
        print(f"Failed to decode message: {err}")
        print(f"Failed to decode message: {body}")
        return

    print(f'Working with... {msg.ID} \n {msg.Text}')
    elevation = extractor.elevation(msg.Text)
    min, max = extractor.min_max_elevation_in_meters(elevation)
    dwc = {
        'country': extractor.country(msg.Text),
        'minimumElevationInMeters': min,
        'maximumElevationInMeters': max,
        'verbatimElevation': elevation,
        #'scientificName': fuzzy_search_python.get_scientific_name(msg.Text),
        'eventDate': extractor.date(msg.Text),
        'scientificName': extractor.scientific_name(msg.Text),
        'agents': extractor.names_known_collectors(msg.Text, 'IT')
    }
    response = {k: v for k, v in dwc.items() if v is not None}
    # except Exception as err:
    #     print(f"Error running extractor: {err}")
    #     return
    print(f'DONE {msg.ID}')
    print(msg.Text)
    print('Converted to:')
    print(response)
    try:
        new_msg = Message(ID=msg.ID, Text=json.dumps(response))
        msg_bytes = json.dumps(new_msg._asdict())
        publish(msg_bytes)
    except Exception as err:
        print(f"Failed to encode message: {err}")
    
    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
    t.start()
    threads.append(t)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBIT_MQ_URI")))
    channel = connection.channel()

    in_queue = channel.queue_declare(queue=os.getenv("INPUT_QUEUE_PYTHON_DWC")) # , auto_delete=True) durable=True
    channel.basic_qos(prefetch_count=1)
    threads = []
    on_message_callback = functools.partial(on_message, args=(connection, threads))
    channel.basic_consume(queue=in_queue.method.queue, on_message_callback=on_message_callback)

    try:
        print('Subscribed to testing, waiting for messages...')
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    connection.close()

if __name__ == '__main__':
    main()
