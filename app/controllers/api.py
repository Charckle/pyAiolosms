from flask import Blueprint, jsonify, request

from app.models import UserM
from app.sending import SendRejected, deliver

api_module = Blueprint('api_module', __name__, url_prefix='/api/v1')


def _bearer_user():
    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        return None
    return UserM.by_token(token.strip())


@api_module.route('/sms', methods=['POST'])
def send_sms():
    user = _bearer_user()
    if not user:
        return jsonify(error='Invalid token.'), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error='Send a JSON object with "to" and "message".'), 400

    try:
        result = deliver(user, payload.get('to', ''), payload.get('message', ''))
    except SendRejected as exc:
        return jsonify(error=str(exc)), exc.status_code

    return jsonify(result), 202
