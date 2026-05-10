from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from models.attendance import Attendance
from models.password_reset import PasswordReset

import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth_bp = Blueprint('auth', __name__)

def generate_recovery_code():
    """
    Generar código numérico de 6 dígitos.
    """
    return str(random.randint(100000, 999999))

def send_recovery_email(user, code):
    """
    Enviar el código de recuperación al correo único del administrador.
    """

    admin_email = os.getenv('ADMIN_RECOVERY_EMAIL')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([admin_email, smtp_server, smtp_email, smtp_password]):
        raise Exception('Faltan datos SMTP en el archivo .env')

    subject = 'Código de recuperación de contraseña - QuickStore'

    body = f"""
    SISTEMA QUICKSTORE - RECUPERACIÓN DE CONTRASEÑA

    Se solicitó recuperar la contraseña del siguiente usuario:

    Código: {user['codigo']}
    Nombre: {user['nombre']}
    Rol: {user['rol']}

    Código de verificación:
    {code}

    Este código tiene validez limitada.
    Si usted no solicitó esta recuperación, ignore este mensaje.
    """

    message = MIMEMultipart()
    message['From'] = smtp_email
    message['To'] = admin_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain', 'utf-8'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_email, smtp_password)
    server.send_message(message)
    server.quit()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        codigo = request.form.get('username')
        password = request.form.get('password')

        if not codigo or not password:
            flash('Código y contraseña son requeridos', 'danger')
            return render_template('login.html')

        user = User.find_by_username(codigo)

        if user and User.verify_password(user, password):
            session.clear()
            session['user_id'] = user['codigo']
            session['username'] = user['codigo']
            session['full_name'] = user['nombre']
            session['rol'] = user['rol']

            Attendance.register_login_action(user['codigo'], 'INICIO DE SESIÓN')

            flash(f'Bienvenido {user["nombre"]}', 'success')
            return redirect(url_for('dashboard'))  # Redirigir al dashboard
        else:
            flash('Código o contraseña incorrectos', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        Attendance.register_login_action(session['user_id'], 'CIERRE DE SESIÓN')

    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))  # Redirigir al login


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Pantalla para solicitar recuperación de contraseña.
    El usuario ingresa su código y el sistema envía un código temporal al correo del administrador.
    """

    if request.method == 'POST':
        codigo = request.form.get('codigo')

        if not codigo:
            flash('Debe ingresar el código de usuario', 'danger')
            return render_template('forgot_password.html')

        user = User.find_by_username(codigo)

        if not user:
            flash('No se encontró un usuario activo con ese código', 'danger')
            return render_template('forgot_password.html')

        recovery_code = generate_recovery_code()

        try:
            PasswordReset.create_reset_code(user['codigo'], recovery_code, minutes_valid=10)
            send_recovery_email(user, recovery_code)

            flash('Se envió un código de recuperación al correo del administrador.', 'success')
            return redirect(url_for('auth.reset_password'))

        except Exception as e:
            flash(f'No se pudo enviar el correo de recuperación: {str(e)}', 'danger')
            return render_template('forgot_password.html')

    return render_template('forgot_password.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    Validar código temporal y cambiar contraseña.
    """

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        recovery_code = request.form.get('recovery_code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([codigo, recovery_code, new_password, confirm_password]):
            flash('Todos los campos son obligatorios', 'danger')
            return render_template('reset_password.html')

        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('reset_password.html')

        if len(new_password) < 3:
            flash('La contraseña debe tener al menos 3 caracteres', 'danger')
            return render_template('reset_password.html')

        user = User.find_by_username(codigo)

        if not user:
            flash('Usuario no encontrado o inactivo', 'danger')
            return render_template('reset_password.html')

        valid_code = PasswordReset.verify_code(codigo, recovery_code)

        if not valid_code:
            flash('El código es incorrecto, ya fue usado o expiró', 'danger')
            return render_template('reset_password.html')

        updated_user = User.update_password(codigo, new_password)

        if updated_user:
            PasswordReset.mark_as_used(valid_code['id'])
            Attendance.register_login_action(codigo, 'RECUPERACIÓN DE CONTRASEÑA')

            flash('Contraseña actualizada correctamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('No se pudo actualizar la contraseña', 'danger')

    return render_template('reset_password.html')