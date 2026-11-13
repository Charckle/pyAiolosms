from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.forms import UserForm
from app.models import UserM, present_user
from app.roles import UserRole, role_label
from app.wrappers import access_required

admin_module = Blueprint('admin_module', __name__, url_prefix='/admin')


def _flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'error')


@admin_module.route('/users/', methods=['GET'])
@access_required(UserRole.ADMIN)
def users_all():
    users = [present_user(u) for u in UserM.get_all()]
    return render_template('admin/users_all.html', users=users, role_label=role_label)


@admin_module.route('/users/new/', methods=['GET', 'POST'])
@access_required(UserRole.ADMIN)
def user_new():
    form = UserForm()
    form.id.data = 'new'

    if form.validate_on_submit():
        if not form.password.data:
            flash('Password is required for a new user.', 'error')
            return render_template('admin/user_form.html', form=form, title='New User', action='new')

        user_id = UserM.create(
            username=form.username.data,
            password=form.password.data,
            role=int(form.role.data),
            status=int(form.status.data),
        )
        flash(f'User "{form.username.data}" created.', 'success')
        return redirect(url_for('admin_module.user_edit', user_id=user_id))

    _flash_form_errors(form)
    return render_template('admin/user_form.html', form=form, title='New User', action='new')


@admin_module.route('/users/<int:user_id>/edit/', methods=['GET', 'POST'])
@access_required(UserRole.ADMIN)
def user_edit(user_id):
    user = UserM.get_one(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_module.users_all'))

    form = UserForm()
    form.id.data = str(user_id)
    issued = None

    if request.method == 'GET':
        form.username.data = user['username']
        form.role.data = str(user['role'])
        form.status.data = str(user['status'])
        pending = session.get('issued_token')
        if pending and pending.get('user_id') == user_id:
            session.pop('issued_token', None)
            issued = pending.get('token')

    elif form.validate_on_submit():
        if (user['status'] == 1 and int(form.status.data) == 0 and UserM.count_active() < 2):
            flash('Cannot disable the last active user.', 'error')
            return redirect(url_for('admin_module.user_edit', user_id=user_id))

        demoting_last_admin = (
            user['role'] == UserRole.ADMIN.value
            and user['status'] == 1
            and (int(form.role.data) != UserRole.ADMIN.value or int(form.status.data) != 1)
            and UserM.count_active_admins() < 2
        )
        if demoting_last_admin:
            flash('Cannot remove the last active admin.', 'error')
            return redirect(url_for('admin_module.user_edit', user_id=user_id))

        UserM.update(
            id_=user_id,
            username=form.username.data,
            role=int(form.role.data),
            status=int(form.status.data),
            password=form.password.data or None,
        )
        flash(f'User "{form.username.data}" updated.', 'success')
        return redirect(url_for('admin_module.user_edit', user_id=user_id))

    else:
        _flash_form_errors(form)

    return render_template(
        'admin/user_form.html',
        form=form,
        title='Edit User',
        action='edit',
        user=present_user(user),
        issued_token=issued,
    )


@admin_module.route('/users/<int:user_id>/delete/', methods=['POST'])
@access_required(UserRole.ADMIN)
def user_delete(user_id):
    user = UserM.get_one(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_module.users_all'))

    if len(UserM.get_all()) < 2:
        flash('Cannot delete the last user.', 'error')
        return redirect(url_for('admin_module.users_all'))

    if user_id == session.get('user_id'):
        flash('Cannot delete yourself.', 'error')
        return redirect(url_for('admin_module.user_edit', user_id=user_id))

    if (user['role'] == UserRole.ADMIN.value and user['status'] == 1
            and UserM.count_active_admins() < 2):
        flash('Cannot delete the last active admin.', 'error')
        return redirect(url_for('admin_module.user_edit', user_id=user_id))

    confirm = request.form.get('confirm_username', '').strip()
    if confirm != user['username']:
        flash('Type the username exactly to confirm deletion.', 'error')
        return redirect(url_for('admin_module.user_edit', user_id=user_id))

    UserM.delete(user_id)
    flash(f'User "{user["username"]}" deleted.', 'success')
    return redirect(url_for('admin_module.users_all'))


@admin_module.route('/users/<int:user_id>/token/', methods=['POST'])
@access_required(UserRole.ADMIN)
def user_token_issue(user_id):
    user = UserM.get_one(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_module.users_all'))

    raw = UserM.issue_token(user_id)
    session['issued_token'] = {'user_id': user_id, 'token': raw}
    flash('API token created. Copy it now. It will not be shown again.', 'success')
    return redirect(url_for('admin_module.user_edit', user_id=user_id))


@admin_module.route('/users/<int:user_id>/token/revoke/', methods=['POST'])
@access_required(UserRole.ADMIN)
def user_token_revoke(user_id):
    user = UserM.get_one(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_module.users_all'))

    UserM.revoke_token(user_id)
    session.pop('issued_token', None)
    flash(f'API token for "{user["username"]}" revoked.', 'success')
    return redirect(url_for('admin_module.user_edit', user_id=user_id))
