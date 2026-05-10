from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from utils.decorators import login_required, permission_required

user_bp = Blueprint('users', __name__, url_prefix='/users')


@user_bp.route('/')
@login_required
@permission_required('user_read')
def list_users():
    """Listar usuarios"""
    users = User.get_all()
    return render_template('users/list.html', users=users)


@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('user_create')
def create_user():
    """Crear usuario"""
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form.get('nombre')
        ci = request.form.get('ci')
        password = request.form.get('password')
        rol = request.form.get('rol')  # 'cajero' o 'admin'

        if not all([codigo, nombre, password, rol]):
            flash('Código, nombre, contraseña y rol son requeridos', 'danger')
            return render_template('users/create.html')

        if len(password) < 3:
            flash('La contraseña debe tener al menos 3 caracteres', 'danger')
            return render_template('users/create.html')

        try:
            user = User.create(codigo, password, nombre, ci, rol)

            if user:
                flash(f'Usuario {user["nombre"]} creado exitosamente', 'success')
                return redirect(url_for('users.list_users'))
            else:
                flash('Error al crear el usuario', 'danger')

        except Exception as e:
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    return render_template('users/create.html')


@user_bp.route('/edit/<user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('user_update')
def edit_user(user_id):
    """Editar usuario"""
    user = User.find_by_id(user_id)

    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ci = request.form.get('ci')
        rol = request.form.get('rol')
        estado = request.form.get('estado') == 'on'

        updated_user = User.update(
            user_id,
            nombre=nombre,
            ci=ci,
            rol=rol,
            estado=estado
        )

        if updated_user:
            flash(f'Usuario {updated_user["nombre"]} actualizado exitosamente', 'success')
            return redirect(url_for('users.list_users'))
        else:
            flash('Error al actualizar el usuario', 'danger')

    return render_template('users/edit.html', user=user)


@user_bp.route('/delete/<user_id>')
@login_required
@permission_required('user_delete')
def delete_user(user_id):
    """Eliminar usuario"""
    if user_id == session.get('user_id'):
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('users.list_users'))

    result = User.delete(user_id)

    if result:
        flash('Usuario eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar el usuario', 'danger')

    return redirect(url_for('users.list_users'))