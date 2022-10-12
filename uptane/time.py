import time


def get_fut24_epoch_time() -> int:
    '''
    Get future epoch time which is 24 hrs from now
    '''
    return int(time.time() + (24 * 60 * 60))


def fut24_is_expired(fut24_time: int) -> bool:
    if fut24_time < time.time():
        return True
    else:
        return False
