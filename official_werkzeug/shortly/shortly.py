import json
import pathlib
import urllib.parse
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Map, Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware


class Shortly:
    """WSGIアプリケーション

    公式チュートリアルではRedisを使っていたが、ここではJSONで代用
    """
    JSON_PATH = pathlib.Path('./shortly.json')

    def __init__(self):
        template_path = pathlib.Path('./templates')
        # TODO Environmentクラスの詳細
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_path)),
                                     autoescape=True)

        # ルーティング
        # TODO MapとRuleの詳細
        self.url_map = Map([
            # endpointの方は、URLの逆引きの時に使う：チュートリアルでは取り扱わない
            Rule('/', endpoint='new_url'),
            Rule('/<short_id>', endpoint='follow_short_link'),
            Rule('/<short_id>+', endpoint='short_link_details'),
        ])

    def dispatch_request(self, request):
        # TODO bind_to_environ()とは？ URLAdapterが返ってくるらしい
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            # このチュートリアルでは、on_<endpoint>という名称のメソッドを呼び出す
            return getattr(self, f'on_{endpoint}')(request, **values)
        except HTTPException as e:
            # except HTTPException, e はPython2の古い書き方
            return e

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype='text/html')

    def insert_url(self, url):
        json_data = {}
        if self.JSON_PATH.exists():
            with self.JSON_PATH.open('r') as f:
                json_data = json.load(f)
            short_id = json_data.get(f'reverse-url:{url}')
            if short_id is not None:
                return short_id

        now = datetime.now()
        stamp = datetime.strftime(now, '%Y%m%d%H%M%S')
        short_id = base36_encode(int(stamp))
        json_data[f'url-target:{short_id}'] = url
        json_data[f'reverse-url:{url}'] = short_id
        with self.JSON_PATH.open('w') as f:
            json.dump(json_data, f)
        return short_id

    def on_new_url(self, request):
        error = None
        url = ''
        if request.method == 'POST':
            # TODO request.form とは
            url = request.form['url']
            if not is_valid_url(url):
                error = 'Please enter a valid URL'
            else:
                short_id = self.insert_url(url)
                return redirect(f'/{short_id}+')
        return self.render_template('new_url.html', error=error, url=url)

    def on_follow_short_link(self, request, short_id):
        with self.JSON_PATH.open('r') as f:
            json_data = json.load(f)
        link_target = json_data.get(f'url-target:{short_id}')
        if link_target is None:
            raise NotFound()
        return redirect(link_target)

    def on_short_link_details(self, request, short_id):
        with self.JSON_PATH.open('r') as f:
            json_data = json.load(f)
        link_target = json_data.get(f'url-target:{short_id}')
        if link_target is None:
            raise NotFound()
        return self.render_template('short_link_details.html',
                                    link_target=link_target,
                                    short_id=short_id,
                                    )

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """WSGIアプリを直接dispatchすることで、wsgi_app()をWSGIミドルウェアっぽく使える"""
        return self.wsgi_app(environ, start_response)


def is_valid_url(url):
    parts = urllib.parse.urlparse(url)
    return parts.scheme in ('http', 'https')


def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))


def create_app(with_static=True):
    app = Shortly()

    if with_static:
        app.wsgi_app = SharedDataMiddleware(
            app.wsgi_app,
            {'/static': str(pathlib.Path('./static'))}
        )
    return app


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    a = create_app()
    run_simple('127.0.0.1', 5000, a, use_debugger=True, use_reloader=True)

