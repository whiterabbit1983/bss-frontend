import uuid
import pika
import click
from compiler import compile


@click.command()
@click.option('-s', '--source-file', required=True)
def main(source_file):
    response = None

    def on_response(ch, method, props, body):
        nonlocal response
        if corr_id == props.correlation_id:
            response = body

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='192.168.1.5', port=5673, 
        credentials=pika.PlainCredentials('guest', 'guest')
    ))
    channel = connection.channel()
    result = channel.queue_declare(exclusive=True)
    callback_queue = result.method.queue
    channel.basic_consume(on_response, no_ack=True, queue=callback_queue)
    corr_id = str(uuid.uuid4())
    body = compile(open(source_file).read())
    print('==> compiled: ', body)
    channel.basic_publish(
        exchange='',
        routing_key='exec',
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id
        ),
        body=body
    )
    while response is None:
        connection.process_data_events()
    print('-->', response)


main()
