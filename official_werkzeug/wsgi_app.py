from werkzeug.wrappers import Response, Request


def application(environ, start_response):
    response = Response('Hello world!', mimetype='text/plain')
    return response(environ, start_response)


def application_expand(environ, start_response):
    request = Request(environ)
    text = f'Hello {request.args.get("name", "World")}!\n'
    response = Response(text, mimetype='text/plain')
    return response(environ, start_response)


if __name__ == '__main__':
    from wsgiref import simple_server
    # server = simple_server.make_server('', 8080, application)

    server = simple_server.make_server('', 8080, application_expand)
    # =>
    # $ curl localhost:8080?name=Mike
    # Hello Mike!

    server.serve_forever()
