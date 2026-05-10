from database.connection import db


class Permission:

    @staticmethod
    def get_all():
        """Obtener todos los permisos desde la tabla modulo/permiso"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id, 
                    p.nombre, 
                    p.descripcion, 
                    m.nombre AS modulo
                FROM public.permiso p
                JOIN public.modulo m ON p.id_modulo = m.id
                ORDER BY m.nombre, p.nombre
            """)

            return cursor.fetchall()

    @staticmethod
    def get_user_permissions(codigo_usuario):
        """Obtener permisos de un usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    p.id, 
                    p.nombre, 
                    p.descripcion, 
                    m.nombre AS modulo
                FROM public.permiso p
                JOIN public.usuario_permiso up ON p.id = up.id_permiso
                JOIN public.modulo m ON p.id_modulo = m.id
                WHERE up.codigo_usuario = %s
                ORDER BY m.nombre, p.nombre
            """, (codigo_usuario,))

            return cursor.fetchall()

    @staticmethod
    def assign_permission(codigo_usuario, permission_id):
        """Asignar permiso a usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.usuario_permiso (
                    codigo_usuario, 
                    id_permiso
                )
                VALUES (%s, %s)
                ON CONFLICT (codigo_usuario, id_permiso) DO NOTHING
                RETURNING codigo_usuario, id_permiso
            """, (codigo_usuario, permission_id))

            return cursor.fetchone()

    @staticmethod
    def remove_permission(codigo_usuario, permission_id):
        """Remover permiso de usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM public.usuario_permiso
                WHERE codigo_usuario = %s 
                AND id_permiso = %s
                RETURNING codigo_usuario, id_permiso
            """, (codigo_usuario, permission_id))

            return cursor.fetchone()

    @staticmethod
    def has_permission(codigo_usuario, permission_name):
        """Verificar si un usuario tiene un permiso específico"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT rol
                FROM public.usuario
                WHERE codigo = %s 
                AND estado = true
            """, (codigo_usuario,))

            user = cursor.fetchone()

            if not user:
                return False

            if user['rol'] == 'admin':
                return True

            cursor.execute("""
                SELECT 1
                FROM public.usuario_permiso up
                JOIN public.permiso p ON up.id_permiso = p.id
                WHERE up.codigo_usuario = %s
                AND p.nombre = %s
                LIMIT 1
            """, (codigo_usuario, permission_name))

            return cursor.fetchone() is not None