from flask import Flask, render_template, session, redirect, url_for, request
from config import config

from models.user import User
from models.client import Client
from models.attendance import Attendance
from models.permission import Permission
from models.product import Product  # Asegúrate de que el modelo de Producto esté importado

from utils.decorators import login_required

from controllers.auth_controller import auth_bp
from controllers.user_controller import user_bp
from controllers.permission_controller import permission_bp
from controllers.client_controller import client_bp
from controllers.attendance_controller import attendance_bp
from controllers.product_controller import product_bp  # Importamos el Blueprint de productos

app = Flask(__name__)
app.config.from_object(config['development'])


@app.before_request
def clear_session_if_needed():
    """
    Control de sesión.
    Permite entrar al login, logout, recuperación de contraseña y archivos estáticos.
    Si no hay sesión, manda al login.
    """
    allowed_routes = [
        'auth.login',
        'auth.logout',
        'auth.forgot_password',
        'auth.reset_password',
        'static'
    ]

    if request.endpoint in allowed_routes:
        return None

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))


# Registra todos los Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(permission_bp)
app.register_blueprint(client_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(product_bp, url_prefix='/products')  # Registra el Blueprint de Productos

# Rutas principales
@app.route('/')
def index():
    """
    Entrada principal del sistema.
    Si no hay sesión, muestra login.
    Si hay sesión, manda al dashboard.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal con bloques según permisos"""

    codigo_usuario = session.get('user_id')

    # Verificación de permisos para cada módulo
    can_view_users = Permission.has_permission(codigo_usuario, 'user_read')
    can_view_clients = Permission.has_permission(codigo_usuario, 'client_read')
    can_view_attendance = Permission.has_permission(codigo_usuario, 'attendance_read')
    can_view_permissions = Permission.has_permission(codigo_usuario, 'permission_read')
    can_view_products = Permission.has_permission(codigo_usuario, 'product_read')  # Verificación de permisos de productos

    stats = {}

    # Estadísticas para cada módulo según los permisos
    if can_view_users:
        users = User.get_all()
        stats['users'] = len(users)

    if can_view_clients:
        clients = Client.get_all()
        stats['clients'] = len(clients)

    if can_view_attendance:
        today_attendance = Attendance.get_today_actions()
        stats['today_attendance'] = len(today_attendance)

    if can_view_permissions:
        permissions = Permission.get_all()
        stats['permissions'] = len(permissions)

    if can_view_products:  # Solo cuenta los productos si tiene el permiso
        products = Product.get_all()  # Asegúrate de que este método devuelva los productos
        stats['products'] = len(products)  # Contamos cuántos productos hay

    # Diccionario con permisos para mostrar los bloques correspondientes
    permissions_dashboard = {
        'can_view_users': can_view_users,
        'can_view_clients': can_view_clients,
        'can_view_attendance': can_view_attendance,
        'can_view_permissions': can_view_permissions,
        'can_view_products': can_view_products  # Incluir la verificación de productos
    }

    # Renderiza el dashboard con las estadísticas y los permisos
    return render_template(
        'dashboard.html',
        stats=stats,
        permissions_dashboard=permissions_dashboard
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)