from flask import request

from formencode import Invalid

from datahub.core import app
from datahub.util import response_format, jsonify
from datahub import views

@app.errorhandler(404)
def handle_exceptions(exc):
    format = response_format(app, request)
    if format == 'json':
        body = {'status': exc.code,
                'name': exc.name,
                'description': exc.get_description(request.environ)}
        return jsonify(body, status=exc.code,
                       headers=exc.get_headers(request.environ))
    return exc

@app.errorhandler(Invalid)
def handle_invalid(exc):
    format = response_format(app, request)
    if format == 'json':
        body = {'status': 400,
                'name': 'Invalid Data',
                'description': unicode(exc),
                'errors': exc.unpack_errors()}
        return jsonify(body, status=400)
    return exc


if __name__ == "__main__":
    app.run()
