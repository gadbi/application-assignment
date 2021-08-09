# application-assignment
I use Flask for web client.
To get all patients just type this URL in your browser: http://localhost:5012
 
API  :  @app.route('/') in \application-assignment\ConsumerService\consumer\main.py 
To get only 1 patient enter to input text "Get patient" the ID of the patient and click submit 
 
API : @app.route('/') in \application-assignment\ConsumerService\consumer\main.py

Rabbitmq : 
You can be counting and push event to the 'events' queue the listener will process the event and save to PostgreSQL   "on_message" in \application-assignment\ConsumerService\consumer\main.py

PostgreSQL    :
Events table created in order to save  the events 
 




