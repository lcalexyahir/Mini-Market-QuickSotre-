from database.connection import db


class Attendance:

    @staticmethod
    def register_login_action(codigo_usuario, accion='INICIO DE SESIÓN'):
        """Registrar automáticamente la acción del usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.historial (
                    codigo_usuario,
                    accion,
                    tabla_afectada,
                    id_registro_afectado,
                    valor_nuevo,
                    fecha_hora
                )
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, codigo_usuario, accion, fecha_hora
            """, (
                codigo_usuario,
                accion,
                'usuario',
                codigo_usuario,
                f'El usuario realizó la acción: {accion}'
            ))

            return cursor.fetchone()

    @staticmethod
    def get_today_actions():
        """Obtener acciones realizadas hoy"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.codigo_usuario,
                    u.nombre,
                    u.rol,
                    h.accion,
                    h.fecha_hora
                FROM public.historial h
                JOIN public.usuario u ON h.codigo_usuario = u.codigo
                WHERE DATE(h.fecha_hora) = CURRENT_DATE
                ORDER BY h.fecha_hora DESC
            """)

            return cursor.fetchall()

    @staticmethod
    def get_all_actions(limit=100):
        """Obtener historial general de acciones"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    h.id,
                    h.codigo_usuario,
                    u.nombre,
                    u.rol,
                    h.accion,
                    h.fecha_hora
                FROM public.historial h
                JOIN public.usuario u ON h.codigo_usuario = u.codigo
                ORDER BY h.fecha_hora DESC
                LIMIT %s
            """, (limit,))

            return cursor.fetchall()