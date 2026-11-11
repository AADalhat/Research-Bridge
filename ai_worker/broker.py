import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends.redis import RedisBackend
from dramatiq.middleware import AgeLimit, TimeLimit, Retries

from config import config

# Setup Redis Backend for result storage
result_backend = RedisBackend(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

# Setup Redis Broker
redis_broker = RedisBroker(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

# Add Results Middleware to allow querying task results via message.get_result()
redis_broker.add_middleware(Results(backend=result_backend))

# Set as default Dramatiq broker
dramatiq.set_broker(redis_broker)

def get_broker():
    return redis_broker

def get_result_backend():
    return result_backend

