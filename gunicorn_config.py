import gunicorn

gunicorn.SERVER = "pyAiolosms"

# One worker keeps SQLite writes simple.
workers = 1
bind = "0.0.0.0:5000"
timeout = 120
