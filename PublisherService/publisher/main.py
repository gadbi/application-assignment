import json
import asyncio
import json
import os

from aio_pika import connect, ExchangeType, Message, DeliveryMode


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_events(loop))

async def update_events(loop):
    connection, exchange = await setup_rabbitmq(loop)
    await publish_events(exchange)
    await connection.close()

async def setup_rabbitmq(loop):
    connection = await connect(host=os.environ.get('RABBIT_HOST'),
                               login=os.environ.get('RABBIT_USER'),
                               password=os.environ.get('RABBIT_PASS'),
                               loop=loop
                               )
    # Creating a channel
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "meds", ExchangeType.FANOUT
    )
    queue = await channel.declare_queue(name='events', auto_delete=True)

    await queue.bind(exchange, "new.events")
    return connection, exchange


async def publish_events(exchange):
    # Get the current working directory of the events.json file
    cwd = os.getcwd()  
    event_json_file_path = ''
    for root, dirs, files in os.walk(cwd):
        if "events.json" in files:
            event_json_file_path=os.path.join(root, "events.json")
    print(event_json_file_path)
    
    with open(event_json_file_path) as f:
        events = json.load(f)
        for event in events:
            message = Message(
                json.dumps(event).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            await exchange.publish(message, routing_key="new.events")
        print("pushed all events to RabbitMQ")


if __name__ == '__main__':
    main()
