from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PyQt6.QtCore import QByteArray

class WebEngineUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    def requestStarted(self, request):
        data = QByteArray()
        try:
            with open(request.requestUrl().path()[1:], 'rb') as f:
                data = QByteArray(f.read())
        except Exception as e:
            print(f"Failed to open file: {e}")
        buf = data
        request.reply(buf)
