from database.connection import db

class Product:
    @staticmethod
    def create(name, price, stock):
        """Crear nuevo producto"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO public.producto (nombre, precio_venta, stock_minimo)
                VALUES (%s, %s, %s)
                RETURNING id, nombre, precio_venta, stock_minimo
            """, (name, price, stock))
            return cursor.fetchone()

    @staticmethod
    def get_all():
        """Obtener todos los productos"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, precio_venta, stock_minimo 
                FROM public.producto
                ORDER BY nombre
            """)
            return cursor.fetchall()

    @staticmethod
    def find_by_id(product_id):
        """Buscar producto por ID"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, precio_venta, stock_minimo
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
                SET nombre = %s, precio_venta = %s, stock_minimo = %s
                WHERE id = %s
                RETURNING id, nombre, precio_venta, stock_minimo
            """, (name, price, stock, product_id))
            return cursor.fetchone()

    @staticmethod
    def delete(product_id):
        """Eliminar producto"""
        with db.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM public.producto WHERE id = %s RETURNING id
            """, (product_id,))
            return cursor.fetchone()