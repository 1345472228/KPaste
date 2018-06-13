import logging

def init_app(app):
    fmt = logging.Formatter('%(asctime)s [%(levelname)s]: (In function %(funcName)s) %(message)s')
    _InfoHandler = logging.FileHandler('log/info.log')
    _ErrorHandler = logging.FileHandler('log/error.log')
    _WarningHandler = logging.FileHandler('log/warn.log')
    _InfoHandler.setLevel(logging.INFO)
    _ErrorHandler.setLevel(logging.DEBUG)
    _WarningHandler.setLevel(logging.WARNING)
    handlers = [_ErrorHandler, _InfoHandler, _WarningHandler]
    for h in handlers:
        h.setFormatter(fmt)
        app.logger.addHandler(h)

