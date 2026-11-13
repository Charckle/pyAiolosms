from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.forms import SendForm
from app.models import MessageM, UserM
from app.roles import UserRole
from app.sending import SendRejected, deliver
from app.wrappers import access_required

sms_module = Blueprint('sms_module', __name__)


def _scope_user_id():
    user = UserM.get_one(session['user_id'])
    if user['role'] == UserRole.ADMIN.value:
        return None
    return user['id']


@sms_module.route('/send/', methods=['GET', 'POST'])
@access_required(UserRole.READWRITE)
def send():
    form = SendForm()
    user = UserM.get_one(session['user_id'])

    if form.validate_on_submit():
        try:
            result = deliver(user, form.to.data, form.message.data)
        except SendRejected as exc:
            flash(str(exc), 'error')
        else:
            flash(f'SMS accepted for {result["destination"]}.', 'success')
            return redirect(url_for('sms_module.log'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')

    return render_template('sms/send.html', form=form)


@sms_module.route('/messages/', methods=['GET'])
@access_required()
def log():
    user_filter = _scope_user_id()
    return render_template(
        'sms/log.html',
        messages=MessageM.recent(200, user_filter),
        showing_all=user_filter is None,
    )
