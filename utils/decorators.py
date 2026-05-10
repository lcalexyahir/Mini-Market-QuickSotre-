from functools import wraps
from flask import session, flash, redirect, url_for, request, jsonify

def login_required(f):
    """Decorador para requerir inicio de sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_name):
    """Decorador para requerir permisos específicos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Por favor inicia sesión para continuar', 'warning')
                return redirect(url_for('auth.login'))
            
            from models.permission import Permission
            if not Permission.has_permission(session['user_id'], permission_name):
                flash('No tienes permiso para acceder a esta sección', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorador para requerir permisos de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verificar si es admin (username = 'admin')
        if session.get('username') != 'admin':
            flash('Acceso restringido a administradores', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function