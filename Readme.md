To add admin -:
python add_admin.py

To run the application -:
python main.py

All the API request and response from the postman

upgrade db-: 
1) flask db stamp head
2) flask db migrate
3) flask db upgrade

To run the celery server -:
celery -A celery_worker.celery worker --loglevel=info

To run redis server -:
redis-server

# text_ai
