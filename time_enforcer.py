import time

class TimeRemainingExpired(Exception):
    pass

# Set time limit to crawling
def enforce_time_remaining(f):
    """ decorator to check time remaining and raise if expired """
    def new_f(*args, **kwargs):
        if kwargs.get('_time_remaining_end_time') is None:
            kwargs['_time_remaining_end_time'] = \
                time.time() + kwargs['time_remaining']
            #print(kwargs['_time_remaining_end_time'])
            #print(kwargs['time_remaining'])
        if time.time() >= kwargs['_time_remaining_end_time']:
            raise TimeRemainingExpired
        return f(*args, **kwargs)

    return new_f
