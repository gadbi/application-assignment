import os
import sys
import asyncio
import logging
import threading
import psycopg2
import json

from aio_pika import connect, IncomingMessage, ExchangeType, Message, DeliveryMode
from flask import Flask,render_template,request

app = Flask(__name__)
loop = asyncio.get_event_loop()

async def setup_rabbitmq(loop):
    connection = await connect(host=os.environ.get('RABBIT_HOST'),
                               login=os.environ.get('RABBIT_USER'),
                               password=os.environ.get('RABBIT_PASS'),
                               loop=loop
                               )

    # Creating a channel
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "events", ExchangeType.DIRECT
    )
    queue = await channel.declare_queue(name='events', auto_delete=True)

    await queue.bind(exchange, "new.events")
    return connection, exchange, queue, channel


async def on_message(message: IncomingMessage):
    async with message.process():
        print(" [x] %r:%r" % (message.routing_key, message.body))
        #logging.info(message.body)
        await insert_events(message.body)
        #message.ack()
        #await asyncio.sleep(0.1)


async def consume_events(loop):
    # Perform connection
    connection, exchange, queue, channel = await setup_rabbitmq(loop)

    await channel.set_qos(prefetch_count=1)

    #await queue.bind(exchange, routing_key="new.events")
    await setup_table_postgres()
    # Start listening the random queue
    consumer_event_tag = await queue.consume(on_message)
  
    try:
        await asyncio.sleep(1000)
    finally:
        logging.info("Before Canceling %s: queue", 'events')
        await queue.cancel(consumer_event_tag)
        logging.info("After Canceling %s: queue", 'events')
        await connection.close()

def listener(name):
    logging.info("Thread %s: starting", name)
    loop.create_task(consume_events(loop))
    loop.run_forever()



async def setup_table_postgres():
    
    logging.info("Connecting to the PostgreSQL database : %s ", os.environ.get('POSTGRES_DB'))
    try:
        connection = psycopg2.connect(host=os.environ.get('POSTGRES_HOST'),
                                      database=os.environ.get('POSTGRES_DB'),
                                      user=os.environ.get('POSTGRES_USER'),
                                      password=os.environ.get('POSTGRES_PASSWORD')
                                      )


        
        # create a cursor
        cur = connection.cursor()
        
        # execute a statement
        cur.execute("select * from information_schema.tables where table_name='events'")
        if bool(cur.rowcount) == False:
            logging.info("Creating events table...")
            sql ='''CREATE TABLE EVENTS(
                p_id CHAR(20) NOT NULL,
                medication_name CHAR(20),
                action CHAR(20),
                event_time CHAR(30)
            )'''
            cur.execute(sql)
            connection.commit()
        else:
            logging.info("Found events table in database")

    
    except (Exception, Error) as error:
        logging.info("Error while connecting to PostgreSQL : %s", error)
    finally:
        cur.close()
        connection.close()


async def pg_connection():
    try:
        connection = psycopg2.connect(host=os.environ.get('POSTGRES_HOST'),
                                      database=os.environ.get('POSTGRES_DB'),
                                      user=os.environ.get('POSTGRES_USER'),
                                      password=os.environ.get('POSTGRES_PASSWORD')
                                      )
        cursor = connection.cursor()
        return connection, cursor
    except Exception as e:
        logging.info("Error connecting to Postgres : %s", e)
        return None 
            

async def insert_events(event_json):  
    connection, cursor = await pg_connection()
    event = json.loads(event_json)
    try:
        event_insert_query = """ INSERT INTO events (p_id, medication_name, action, event_time) VALUES (%s,%s,%s,%s)"""
        event_record_to_insert = (event['p_id'], event['medication_name'], event['action'], event['event_time'])
        cursor.execute(event_insert_query, event_record_to_insert)
        connection.commit()
        logging.info("Patient : %s successfully updated ", event['p_id'])
    except Exception as er:
        logging.info("Error during update the Patient : %s -> Error : %s" ,event['p_id'], err)
    finally:
        if connection:
            cursor.close()
            connection.close()
            logging.info("PostgreSQL connection is closed")

def medication_events(p_id):
    connection = psycopg2.connect(host=os.environ.get('POSTGRES_HOST'),
                                      database=os.environ.get('POSTGRES_DB'),
                                      user=os.environ.get('POSTGRES_USER'),
                                      password=os.environ.get('POSTGRES_PASSWORD')
                                      )
    cursor = connection.cursor()
    eventlist= []
    try:
        
        if p_id == 'NA':
            cursor.execute("SELECT * FROM events;")
        else:
            select_with_pid = "SELECT * FROM events where p_id=%s;"
            cursor.execute(select_with_pid,(p_id,))

        for row in cursor:
            event = list((row[0], row[1], row[2], row[3]))
            eventlist.append(event)  
            logging.info("Event : %s : %s ",row[0],row[1])

    except Exception as er:
        logging.info("Error during creating event  Error : %s" , er)
    finally:
        if connection:
            cursor.close()
            connection.close() 
            logging.info("PostgreSQL connection is closed")
            return eventlist





@app.route('/')
def home():
    eventlist = medication_events('NA')
    return render_template('medication.html',eventlist=eventlist)

@app.route('/patient', methods=['GET', 'POST'])    
def patient():
    p_id = request.args.get('p_id')
    eventlist = medication_events(p_id)
    return render_template('medication.html',eventlist=eventlist)

def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    logging.info("Main    : before creating thread")
    rabbitmq_listener = threading.Thread(target=listener, args=('Rabbitmq listener',))
    logging.info("Main    : before running thread")
    rabbitmq_listener.start() 

    PORT = os.environ.get('CONSUMER_PORT')
    app.run(host='0.0.0.0', port=PORT)
    

if __name__ == '__main__':
     main()
  


