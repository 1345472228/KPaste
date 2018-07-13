import threading
from datetime import timedelta

_expired_check_timer = None
_db = None
interval_sec = timedelta(1).total_seconds()

def init_db(database):
    global _db
    if _db is None:
        _db = database


def _expired_check_timer_handler():
    global _expired_check_timer
    _expired_check_timer = threading.Timer(interval_sec, _expired_check_timer_handler)
    _expired_check_timer.start()
    _db.check_validity()

def begin():
    if _expired_check_timer is None or not _expired_check_timer.is_alive():
        try:
            print('began')
            _expired_check_timer_handler()
            return '[timer.begin]: Timer begin running now.'
        except Exception as e:
            # log(e)
            print('error' + str(e))
            return "[timer.begin]: Some Error occur <>" + str(e)
        finally:
            _db.close_session()
    else:
        print('running')
        return "[timer.begin]: Timer is running."

def stop():
    if _expired_check_timer and _expired_check_timer.is_alive():
        _expired_check_timer.cancel()
        return '[timer.stop]: stopped'
    else:
        print('not begin')
        return '[timer.stop]: Timer is not running.'
