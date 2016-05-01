"""Auth module that uses a QT or GTK browser to prompt the user."""
import signal
from contextlib import contextmanager

from PyQt4 import QtCore, QtGui, QtWebKit

CHECK_AUTH_JS = """
    var code = document.getElementById("code");
    var access_denied = document.getElementById("access_denied");
    var result;
    
    if (code) {
        result = {authorized: true, code: code.value};
    } else if (access_denied) {
        result = {authorized: false, message: access_denied.innerText};
    } else {
        result = {};
    }
    result;
"""

@contextmanager
def default_sigint():
    """Context manager that sets SIGNINT to the default value."""
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, original_sigint_handler)

    WEBKIT_BACKEND = "qt"

def _on_qt_page_load_finished(dialog, webview):
    frame = webview.page().currentFrame()
    res = frame.evaluateJavaScript(CHECK_AUTH_JS)
    authorization = dict((k, v) for (k, v) in res.items())
    if "authorized" in authorization:
        dialog.authorization_code = authorization.get("code")
        dialog.close()

def get_code(url, size=(640, 480), title="Google authentication"):
    """Open a QT webkit window and return the access code."""
    app = QtGui.QApplication([])
    dialog = QtGui.QDialog()
    dialog.setWindowTitle(title)
    dialog.resize(*size)
    webview = QtWebKit.QWebView()
    webpage = QtWebKit.QWebPage()
    webview.setPage(webpage)           
    webpage.loadFinished.connect(lambda: _on_qt_page_load_finished(dialog, webview))
    webview.setUrl(QtCore.QUrl.fromEncoded(url))
    layout = QtGui.QGridLayout()
    layout.addWidget(webview)
    dialog.setLayout(layout)
    dialog.authorization_code = None
    dialog.show()
    app.exec_()
    return dialog.authorization_code
