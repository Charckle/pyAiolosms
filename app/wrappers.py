from functools import wraps
import base64

from flask import flash, redirect, request, session, url_for

from app.models import UserM
from app.roles import UserRole


def _redirect_to_login():
    if UserM.needs_setup():
        return redirect(url_for('main.setup'))

    request_url = request.url
    requested_url = '/' + '/'.join(request_url.split('/')[3:])
    encoded = base64.urlsafe_b64encode(requested_url.encode()).decode()
    flash('Please login to access the site.', 'error')
    return redirect(url_for('main.login', w_url=encoded))


def access_required(min_role: UserRole = None):
    """
    Require a logged-in active user, and optionally a role.

        @access_required()                      # any active user
        @access_required(UserRole.READWRITE)    # read/write or admin
        @access_required(UserRole.ADMIN)        # admin only
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return _redirect_to_login()

            user = UserM.get_one(session['user_id'])
            if not user or user.get('status') != 1:
                session.clear()
                return _redirect_to_login()

            if min_role is None:
                return f(*args, **kwargs)

            user_role = UserRole(user['role'])
            # Lower value = more access: ADMIN=1, READWRITE=2, READ=3
            if user_role.value <= min_role.value:
                return f(*args, **kwargs)

            flash("You don't have access to this page.", 'error')
            return redirect(url_for('main.index'))

        return wrapper
    return decorator
