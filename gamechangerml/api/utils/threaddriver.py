import threading
import json
import sys
from gamechangerml.api.utils.logger import logger
from gamechangerml.api.utils import processmanager

# A class that takes in a function and a dictionary of arguments.
# The keys in args have to match the parameters in the function.
class MlThread(threading.Thread):
    def __init__(self, function, args = {}):
        super(MlThread, self).__init__()
        self.function = function
        self.args = args
        self.killed = False
   
    def run(self):
        try:
            sys.settrace(self.globaltrace)
            self.function(**self.args)
        except Exception as e:
            logger.error(e)
            logger.info("Thread errored out attempting " + self.function.__name__ + " with parameters: " + json.dumps(self.args))

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        logger.info(f'killing {self.function}')
        self.killed = True

# Pass in a function and args which is an array of dicts
# A way to load mulitple jobs and run them on threads.
# join is set to false unless we need to collect the results immediately.
def run_threads(function_list, args_list = [], join = False):
    threads = []
    for i, function in enumerate(function_list):
        args = {}
        if i < len(args_list):
            args = args_list[i]
        thread = MlThread(function, args)  
        threads.append(thread)
        thread.start()
    # If we join the threads the function will wait until they have all completed.
    if join:
        for thread in threads:
            thread.join()