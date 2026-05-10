from database.connection import db
from datetime import datetime, timedelta
import hashlib


class PasswordReset:
    @staticmethod
    def hash_code(code):
        """
        Convertir el código en hash para no guardarlo directamente en la base de datos.
        """
        return hashlib.sha256(code.encode('utf-8')).hexdigest()

    @staticmethod
    def create_reset_code(codigo_usuario, code, minutes_valid=10):
        """
        Crear un código de recuperación con tiempo limitado.
        Antes de crear uno nuevo, invalida los anteriores del mismo usuario.
        """

        code_hash = PasswordReset.hash_code(code)
        expiration = datetime.now() + timedelta(minutes=minutes_valid)

        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.recuperacion_contrasena
                SET usado = true
                WHERE codigo_usuario = %s
                AND usado = false
            """, (codigo_usuario,))

            cursor.execute("""
                INSERT INTO public.recuperacion_contrasena (
                    codigo_usuario,
                    codigo_hash,
                    fecha_expiracion,
                    usado
                )
                VALUES (%s, %s, %s, false)
                RETURNING id, codigo_usuario, fecha_creacion, fecha_expiracion, usado
            """, (codigo_usuario, code_hash, expiration))

            return cursor.fetchone()

    @staticmethod
    def verify_code(codigo_usuario, code):
        """
        Verificar si el código es correcto, no fue usado y no expiró.
        """

        code_hash = PasswordReset.hash_code(code)

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, codigo_usuario, fecha_expiracion, usado
                FROM public.recuperacion_contrasena
                WHERE codigo_usuario = %s
                AND codigo_hash = %s
                AND usado = false
                AND fecha_expiracion >= CURRENT_TIMESTAMP
                ORDER BY fecha_creacion DESC
                LIMIT 1
            """, (codigo_usuario, code_hash))

            return cursor.fetchone()

    @staticmethod
    def mark_as_used(reset_id):
        """
        Marcar el código como usado después de cambiar la contraseña.
        """

        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.recuperacion_contrasena
                SET usado = true
                WHERE id = %s
                RETURNING id
            """, (reset_id,))

            return cursor.fetchone()