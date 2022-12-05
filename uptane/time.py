import time


def get_fut24_epoch_time() -> int:
    '''
    Get future epoch time which is 24 hrs from now
    '''
    return int(time.time() + (24 * 60 * 60))


def get_fut365y_epoch_time() -> int:
    '''
    Get future epoch time which is 356 days from now
    '''
    return int(time.time() + (24 * 60 * 60 * 365))


def fut_is_expired(fut24_time: int) -> bool:
    if fut24_time < time.time():
        return True
    else:
        return False
