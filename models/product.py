from database.connection import db


class Product:

    @staticmethod
    def create(name, price, stock):
        """Crear nuevo producto"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.producto (
                    codigo,
                    nombre,
                    precio_venta,
                    stock_minimo,
                    estado
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    true
                )
                RETURNING id, codigo, nombre, precio_venta, stock_minimo, estado
            """, (
                Product.generate_code(),
                name,
                price,
                stock
            ))

            return cursor.fetchone()

    @staticmethod
    def generate_code():
        """Generar código automático para producto"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT codigo
                FROM public.producto
                WHERE codigo LIKE 'PROD%%'
                ORDER BY codigo DESC
                LIMIT 1
            """)

            last_product = cursor.fetchone()

            if not last_product:
                return 'PROD001'

            last_code = last_product['codigo']
            last_number = int(last_code.replace('PROD', ''))
            new_number = last_number + 1

            return f'PROD{new_number:03d}'

    @staticmethod
    def get_all():
        """Obtener todos los productos activos"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    codigo,
                    nombre,
                    precio_venta,
                    precio_compra,
                    stock_minimo,
                    estado
                FROM public.producto
                WHERE estado = true
                ORDER BY nombre
            """)

            return cursor.fetchall()

    @staticmethod
    def find_by_id(product_id):
        """Buscar producto por ID"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    codigo,
                    nombre,
                    precio_venta,
                    precio_compra,
                    stock_minimo,
                    estado
                FROM public.producto
                WHERE id = %s
            """, (product_id,))

            return cursor.fetchone()

    @staticmethod
    def update(product_id, name, price, stock):
        """Actualizar producto"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.producto
                SET
                    nombre = %s,
                    precio_venta = %s,
                    stock_minimo = %s
                WHERE id = %s
                RETURNING id, codigo, nombre, precio_venta, stock_minimo, estado
            """, (name, price, stock, product_id))

            return cursor.fetchone()

    @staticmethod
    def delete(product_id):
        """Eliminar producto con borrado lógico"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.producto
                SET estado = false
                WHERE id = %s
                RETURNING id
            """, (product_id,))

            return cursor.fetchone()