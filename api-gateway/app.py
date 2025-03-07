from flask import Flask, request, jsonify
import requests
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    user_service_url = app.config['USER_SERVICE_URL']
    url = f"{user_service_url}/{path}"

    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for key, value in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        params=request.args
    )

    response = jsonify(resp.json()) if resp.content else jsonify({})
    response.status_code = resp.status_code

    for key, value in resp.headers.items():
        if key.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']:
            response.headers[key] = value

    return response


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "API Gateway is running",
        "version": "1.0.0"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)