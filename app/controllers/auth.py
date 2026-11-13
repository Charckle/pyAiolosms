import base64

from flask import Blueprint, current_app, flash, redirect, render_template, session, url_for

from app.forms import LoginForm, SetupForm
from app.models import MessageM, UserM, present_user
from app.roles import UserRole
from app.wrappers import access_required

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
@access_required()
def index():
    user = UserM.get_one(session['user_id'])
    own_only = user['role'] != UserRole.ADMIN.value
    user_filter = user['id'] if own_only else None
    return render_template(
        'index.html',
        message_count=MessageM.count(user_filter),
        user_count=len(UserM.get_all()) if not own_only else None,
        recent=MessageM.recent(8, user_filter),
    )


@main.route('/setup/', methods=['GET', 'POST'])
def setup():
    if not UserM.needs_setup():
        return redirect(url_for('main.login'))

    if current_app.config.get('READ_ONLY_MODE'):
        return render_template('auth/setup_readonly.html')

    form = SetupForm()

    if form.validate_on_submit():
        if not UserM.needs_setup():
            return redirect(url_for('main.login'))

        user_id = UserM.create(
            username=form.username.data,
            password=form.password.data,
            role=UserRole.ADMIN.value,
            status=1,
        )
        form.password.data = None
        form.password_2.data = None

        session['user_id'] = user_id
        session['user_role'] = UserRole.ADMIN.value
        session.permanent = True
        flash(f'Admin account "{form.username.data}" created.', 'success')
        return redirect(url_for('main.index'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')

    return render_template('auth/setup.html', form=form)


@main.route('/login/', methods=['GET', 'POST'])
@main.route('/login/<w_url>', methods=['GET', 'POST'])
def login(w_url=None):
    if UserM.needs_setup():
        return redirect(url_for('main.setup'))

    if 'user_id' in session:
        return redirect(url_for('main.index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = UserM.login_check(form.username.data, form.password.data)
        form.password.data = None

        if user:
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session.permanent = True

            if w_url:
                try:
                    dest = base64.urlsafe_b64decode(w_url.encode()).decode()
                    return redirect(dest)
                except Exception:
                    pass

            return redirect(url_for('main.index'))

        flash('Invalid username or password.', 'error')

    return render_template('auth/login.html', form=form, w_url=w_url)


@main.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.login'))


def current_user_row():
    if not session.get('user_id'):
        return None
    return UserM.get_one(session['user_id'])


def current_user_view():
    return present_user(current_user_row())
