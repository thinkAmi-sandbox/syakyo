import os
import urllib.parse
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.utils import redirect
from jinja2 import Environment, FileSystemLoader


class Shortly:
    """WSGIアプリケーション"""
    def __init__(self):
        pass

    def dispatch_request(self, request):
        return Response('Hello world!')

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """WSGIアプリを直接dispatchすることで、wsgi_app()をWSGIミドルウェアっぽく使える"""
        return self.wsgi_app(environ, start_response)


def create_app(with_static=True):
    app = Shortly()

    if with_static:
        app.wsgi_app = SharedDataMiddleware(
            app.wsgi_app,
            {'/static': os.path.join(os.path.dirname(__file__), 'static')}
        )
    return app


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    a = create_app()
    run_simple('127.0.0.1', 5000, a, use_debugger=True, use_reloader=True)

