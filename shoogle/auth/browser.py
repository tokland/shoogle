import signal
from contextlib import contextmanager

@contextmanager
def default_sigint():
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)

try:
    from . import webkit_qt as backend
    WEBKIT_BACKEND = "qt"
except ImportError:
    try:
        from . import webkit_gtk as backend
        WEBKIT_BACKEND = "gtk"
    except ImportError:
        WEBKIT_BACKEND = None

def get_code(url, size=(640, 480), title="Google authentication"):
    if WEBKIT_BACKEND:
        with default_sigint():
            return backend.get_code(url, size=size, title=title)
    else:
        raise NotImplementedError("GUI auth requires pywebkitgtk or qtwebkit")
