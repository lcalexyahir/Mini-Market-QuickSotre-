from database.connection import db


class User:

    @staticmethod
    def find_by_username(codigo):
        """Buscar usuario por código"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    contrasena,
                    nombre,
                    ci,
                    rol,
                    estado,
                    fecha_creacion
                FROM public.usuario
                WHERE codigo = %s
                AND estado = true
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def find_by_id(codigo):
        """Buscar usuario por código"""
        return User.find_by_username(codigo)

    @staticmethod
    def get_all(active_only=True):
        """Obtener todos los usuarios"""
        with db.get_cursor() as cursor:
            query = """
                SELECT
                    codigo,
                    nombre,
                    ci,
                    rol,
                    estado,
                    fecha_creacion
                FROM public.usuario
            """

            if active_only:
                query += " WHERE estado = true"

            query += " ORDER BY codigo"

            cursor.execute(query)

            return cursor.fetchall()

    @staticmethod
    def create(codigo, password, nombre, ci, rol):
        """Crear nuevo usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.usuario (
                    codigo,
                    contrasena,
                    nombre,
                    ci,
                    rol,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, true)
                RETURNING codigo, nombre, ci, rol
            """, (codigo, password, nombre, ci, rol))

            return cursor.fetchone()

    @staticmethod
    def update(codigo, **kwargs):
        """Actualizar usuario"""
        allowed_fields = ['nombre', 'ci', 'rol', 'estado']
        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = %s")
                values.append(kwargs[field])

        if not updates:
            return None

        values.append(codigo)

        with db.get_cursor() as cursor:
            cursor.execute(f"""
                UPDATE public.usuario
                SET {', '.join(updates)}
                WHERE codigo = %s
                RETURNING codigo, nombre, ci, rol, estado
            """, values)

            return cursor.fetchone()

    @staticmethod
    def update_password(codigo, new_password):
        """Actualizar contraseña del usuario"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.usuario
                SET contrasena = %s
                WHERE codigo = %s
                AND estado = true
                RETURNING codigo, nombre, rol
            """, (new_password, codigo))

            return cursor.fetchone()

    @staticmethod
    def delete(codigo):
        """Eliminar usuario con borrado lógico"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.usuario
                SET estado = false
                WHERE codigo = %s
                RETURNING codigo
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def verify_password(user, password):
        """Verificar contraseña"""
        if not user or 'contrasena' not in user:
            return False

        return user['contrasena'] == password