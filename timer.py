from flask import g
import threading
from datetime import timedelta

app = None
_expired_check_timer = None
interval_sec = timedelta(1).total_seconds()


def _expired_check_timer_handler():
    global _expired_check_timer
    _expired_check_timer = threading.Timer(interval_sec, _expired_check_timer_handler)
    _expired_check_timer.start()
    g.db.check_validity()


def begin():
    if _expired_check_timer is None or not _expired_check_timer.is_alive():
        try:
            print('began')
            _expired_check_timer_handler()
            return '[timer.begin]: 定时销毁已启动。'
        except Exception as e:
            print('error' + str(e))
            return "[timer.begin]: 额，出错了。\n{}".format(str(e))
        finally:
            g.db.close_session()
    else:
        print('running')
        return "[timer.begin]: 已经在运行了。"


def stop():
    if _expired_check_timer and _expired_check_timer.is_alive():
        _expired_check_timer.cancel()
        return '[timer.stop]: 定时销毁已停止。'
    else:
        print('not begin')
        return '[timer.stop]: 尚未启动。'


def init_app(app_):
    global app
    app = app_
    app.add_url_rule('/timer/begin/', None, begin)
    app.add_url_rule('/timer/stop/', None, stop)
