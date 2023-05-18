from config import REDIS_SERVER, REDIS_PORT

broker_url = 'redis://' + REDIS_SERVER + ':' + str(REDIS_PORT) + '/0'
result_backend = 'redis://' + REDIS_SERVER + ':' + str(REDIS_PORT) + '/0'
