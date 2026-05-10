from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.user import User
from models.permission import Permission
from utils.decorators import login_required, permission_required

permission_bp = Blueprint('permissions', __name__, url_prefix='/permissions')


@permission_bp.route('/')
@login_required
@permission_required('permission_read')
def list_permissions():
    """
    Pantalla principal de gestión de permisos.
    Muestra usuarios para que el administrador pueda asignar permisos.
    """

    users = User.get_all(active_only=False)
    permissions = Permission.get_all()

    return render_template(
        'permissions/list.html',
        users=users,
        permissions=permissions
    )


@permission_bp.route('/assign/<user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('permission_assign')
def assign_permissions(user_id):
    """Asignar permisos a usuario"""

    user = User.find_by_id(user_id)

    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        permission_ids = request.form.getlist('permissions')
        current_perms = Permission.get_user_permissions(user_id)

        for perm in current_perms:
            if str(perm['id']) not in permission_ids:
                Permission.remove_permission(user_id, perm['id'])

        for perm_id in permission_ids:
            Permission.assign_permission(user_id, int(perm_id))

        flash(f'Permisos actualizados para {user["nombre"]}', 'success')
        return redirect(url_for('permissions.list_permissions'))

    all_permissions = Permission.get_all()
    user_permissions = Permission.get_user_permissions(user_id)
    user_perm_ids = [p['id'] for p in user_permissions]

    grouped = {}

    for perm in all_permissions:
        module = perm['modulo']

        if module not in grouped:
            grouped[module] = []

        grouped[module].append({
            **perm,
            'checked': perm['id'] in user_perm_ids
        })

    return render_template(
        'permissions/assign.html',
        user=user,
        grouped_permissions=grouped
    )