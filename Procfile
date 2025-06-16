web: gunicorn src.app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: python src/worker.py
release: python src/init_db.py 