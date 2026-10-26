from .testing import *  # noqa: F403
DATABASES = {"default": dj_database_url.config(default="postgresql://restaurant:restaurant@localhost:5432/restaurant_test", conn_max_age=0)}
