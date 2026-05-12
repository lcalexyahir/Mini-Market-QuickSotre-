import re


def validate_password_strength(password):
    """
    Validar que la contraseña tenga:
    - Mínimo 8 caracteres
    - Una letra mayúscula
    - Una letra minúscula
    - Un número
    - Un signo o carácter especial
    """

    errors = []

    if not password or len(password) < 8:
        errors.append('mínimo 8 caracteres')

    if not re.search(r'[A-Z]', password):
        errors.append('una letra mayúscula')

    if not re.search(r'[a-z]', password):
        errors.append('una letra minúscula')

    if not re.search(r'\d', password):
        errors.append('un número')

    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append('un signo o carácter especial')

    return errors