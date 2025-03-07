from flask import Flask, request, jsonify, send_from_directory
import requests
import os
from config import Config
import yaml
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
app.config.from_object(Config)

SWAGGER_URL = '/api/docs'
API_YAML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openapi.yml')

with open(API_YAML_PATH, 'r') as f:
    api_spec = yaml.safe_load(f)

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    '/api/spec',
    config={
        'app_name': "User Authentication API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/api/spec')
def get_spec():
    return jsonify(api_spec)

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
        "version": "1.0.0",
        "swagger_docs": f"{request.url_root.rstrip('/')}{SWAGGER_URL}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)