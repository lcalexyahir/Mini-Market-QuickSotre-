from database.connection import db


class Provider:

    @staticmethod
    def generate_code():
        """
        Generar código automático para proveedor.
        Ejemplo: PROV001, PROV002, PROV003...
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT codigo
                FROM public.proveedor
                WHERE codigo ~ '^PROV[0-9]+$'
                ORDER BY CAST(SUBSTRING(codigo FROM 5) AS INTEGER) DESC
                LIMIT 1
            """)

            last_provider = cursor.fetchone()

            if not last_provider:
                return 'PROV001'

            last_code = last_provider['codigo']
            last_number = int(last_code.replace('PROV', ''))
            new_number = last_number + 1

            return f'PROV{new_number:03d}'

    @staticmethod
    def get_all():
        """
        Obtener todos los proveedores.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    descripcion,
                    direccion,
                    telefono,
                    email
                FROM public.proveedor
                ORDER BY codigo
            """)

            return cursor.fetchall()

    @staticmethod
    def count_all():
        """
        Contar proveedores registrados.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.proveedor
            """)

            result = cursor.fetchone()
            return result['total'] if result else 0

    @staticmethod
    def find_by_codigo(codigo):
        """
        Buscar proveedor por código.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    descripcion,
                    direccion,
                    telefono,
                    email
                FROM public.proveedor
                WHERE codigo = %s
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def create(nombre, descripcion=None, direccion=None, telefono=None, email=None):
        """
        Crear nuevo proveedor.
        El código se genera automáticamente.
        """
        codigo = Provider.generate_code()

        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.proveedor (
                    codigo,
                    nombre,
                    descripcion,
                    direccion,
                    telefono,
                    email
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING codigo, nombre, descripcion, direccion, telefono, email
            """, (
                codigo,
                nombre,
                descripcion,
                direccion,
                telefono,
                email
            ))

            return cursor.fetchone()

    @staticmethod
    def update(codigo, nombre, descripcion=None, direccion=None, telefono=None, email=None):
        """
        Actualizar proveedor.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.proveedor
                SET
                    nombre = %s,
                    descripcion = %s,
                    direccion = %s,
                    telefono = %s,
                    email = %s
                WHERE codigo = %s
                RETURNING codigo, nombre, descripcion, direccion, telefono, email
            """, (
                nombre,
                descripcion,
                direccion,
                telefono,
                email,
                codigo
            ))

            return cursor.fetchone()

    @staticmethod
    def delete(codigo):
        """
        Eliminar proveedor.

        Antes de eliminar, valida si el proveedor está asociado a productos.
        Esto evita dejar productos con codigo_proveedor huérfano.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.producto
                WHERE codigo_proveedor = %s
            """, (codigo,))

            result = cursor.fetchone()
            total_products = result['total'] if result else 0

            if total_products > 0:
                raise ValueError(
                    'No se puede eliminar este proveedor porque tiene productos asociados.'
                )

            cursor.execute("""
                DELETE FROM public.proveedor
                WHERE codigo = %s
                RETURNING codigo
            """, (codigo,))

            return cursor.fetchone()