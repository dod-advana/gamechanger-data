import os
import redis
import json

from gamechangerml.api.utils.logger import logger

REDIS_HOST = os.environ.get("REDIS_HOST", default="localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", default="6379")
if REDIS_HOST == "":
    REDIS_HOST = "localhost"
if REDIS_PORT == "":
    REDIS_PORT = 6379

# An easy variable interface for redis. 
# Takes in a string key and an optional boolean hash which point 
# to an index in redis and declar if it is a dictionary or not.
# Once initialized use get and set .value with and equals sign.
# Eg: latest_intel_model_sent.value = "foo"
class CacheVariable:
    def __init__(self, key, encode = False):
        self._connection = redis.Redis(connection_pool=RedisPool().getPool())
        self._key = key 
        self._encode = encode
    # Default get method, checks if the key is in redis and gets 
    # the value whether it is a list, dict or standard type
    def get_value(self):
        if(self._connection.exists(self._key)):
            result = self._connection.get(self._key)
            if(self._encode):
                result = json.loads(result)
            return result
        return None
    # Default set method, sets values for dicts and standard types.
    # Note: Should use push if using a list.
    def set_value(self, value):
        if(self._encode):
            value = json.dumps(value)
        return self._connection.set(self._key, value)
    # Default delete method, removes key from redis
    def del_value(self):
        return self._connection.delete(self._key)
    
    value = property(get_value, set_value, del_value)

# A singleton class that creates a connection pool with redis.
# All cache variables use this one connection pool.
class RedisPool:
    __pool = None
    @staticmethod 
    def getPool():
        """ Static access method. """
        if RedisPool.__pool == None:
            RedisPool()
        return RedisPool.__pool
    def __init__(self):
        """ Virtually private constructor. """
        if RedisPool.__pool != None:
            logger.info("Using redis pool singleton")
        else:
            try:
                RedisPool.__pool = redis.ConnectionPool(host=REDIS_HOST, port=int(REDIS_PORT), db = 0, decode_responses=True)
            except Exception as e:
                logger.error(
                    " *** Unable to connect to redis {REDIS_HOST} {REDIS_PORT}***")
                logger.error(e)