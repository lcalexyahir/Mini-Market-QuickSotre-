from database.connection import db


class Warehouse:

    @staticmethod
    def _to_int(value, field_name='valor'):
        """
        Convertir valor a entero de forma segura.
        """
        try:
            number = int(value)
        except Exception:
            raise ValueError(f'El campo {field_name} debe ser un número entero.')

        return number

    @staticmethod
    def _generate_code(cursor):
        """
        Generar código automático para almacén.
        Ejemplo: ALM001, ALM002, ALM003.
        """
        cursor.execute("""
            SELECT codigo
            FROM public.almacen
            WHERE codigo ~ '^ALM[0-9]+$'
            ORDER BY CAST(SUBSTRING(codigo FROM 4) AS INTEGER) DESC
            LIMIT 1
        """)

        last_warehouse = cursor.fetchone()

        if not last_warehouse:
            return 'ALM001'

        last_code = last_warehouse['codigo']
        last_number = int(last_code.replace('ALM', ''))
        new_number = last_number + 1

        return f'ALM{new_number:03d}'

    @staticmethod
    def count_all():
        """
        Contar almacenes registrados.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.almacen
            """)

            result = cursor.fetchone()
            return result['total'] if result else 0

    @staticmethod
    def get_all():
        """
        Listar todos los almacenes.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    direccion,
                    capacidad_actual,
                    capacidad_total
                FROM public.almacen
                ORDER BY codigo
            """)

            return cursor.fetchall()

    @staticmethod
    def find_by_code(codigo):
        """
        Buscar almacén por código.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    direccion,
                    capacidad_actual,
                    capacidad_total
                FROM public.almacen
                WHERE codigo = %s
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def create(nombre, direccion=None, capacidad_total=None):
        """
        Crear nuevo almacén.
        """
        if not nombre:
            raise ValueError('El nombre del almacén es obligatorio.')

        if capacidad_total is None or capacidad_total == '':
            capacidad_total = 0
        else:
            capacidad_total = Warehouse._to_int(capacidad_total, 'capacidad total')

        if capacidad_total < 0:
            raise ValueError('La capacidad total no puede ser negativa.')

        with db.get_cursor() as cursor:
            codigo = Warehouse._generate_code(cursor)

            cursor.execute("""
                INSERT INTO public.almacen (
                    codigo,
                    nombre,
                    direccion,
                    capacidad_actual,
                    capacidad_total
                )
                VALUES (%s, %s, %s, 0, %s)
                RETURNING
                    codigo,
                    nombre,
                    direccion,
                    capacidad_actual,
                    capacidad_total
            """, (
                codigo,
                nombre,
                direccion,
                capacidad_total
            ))

            return cursor.fetchone()

    @staticmethod
    def update(codigo, nombre, direccion=None, capacidad_total=None):
        """
        Actualizar almacén.
        """
        if not nombre:
            raise ValueError('El nombre del almacén es obligatorio.')

        if capacidad_total is None or capacidad_total == '':
            capacidad_total = 0
        else:
            capacidad_total = Warehouse._to_int(capacidad_total, 'capacidad total')

        if capacidad_total < 0:
            raise ValueError('La capacidad total no puede ser negativa.')

        warehouse = Warehouse.find_by_code(codigo)

        if not warehouse:
            raise ValueError('El almacén no existe.')

        capacidad_actual = warehouse['capacidad_actual'] or 0

        if capacidad_total < capacidad_actual:
            raise ValueError(
                'La capacidad total no puede ser menor que la capacidad actual del almacén.'
            )

        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.almacen
                SET
                    nombre = %s,
                    direccion = %s,
                    capacidad_total = %s
                WHERE codigo = %s
                RETURNING
                    codigo,
                    nombre,
                    direccion,
                    capacidad_actual,
                    capacidad_total
            """, (
                nombre,
                direccion,
                capacidad_total,
                codigo
            ))

            return cursor.fetchone()

    @staticmethod
    def delete(codigo):
        """
        Eliminar almacén.
        No permite eliminar si tiene inventario activo.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) AS total
                FROM public.inventario
                WHERE codigo_almacen = %s
                AND estado = true
            """, (codigo,))

            result = cursor.fetchone()
            total_inventory = result['total'] if result else 0

            if total_inventory > 0:
                raise ValueError(
                    'No se puede eliminar este almacén porque tiene productos en inventario.'
                )

            cursor.execute("""
                DELETE FROM public.almacen
                WHERE codigo = %s
                RETURNING codigo
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def get_products_for_inventory():
        """
        Obtener productos activos para entradas de inventario.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
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
    def get_inventory_by_warehouse(codigo_almacen):
        """
        Obtener inventario agrupado por producto dentro de un almacén.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    i.codigo_producto,
                    p.nombre AS producto,
                    COALESCE(SUM(i.cantidad), 0) AS cantidad_total,
                    MAX(i.fecha_entrada) AS ultima_entrada,
                    MIN(i.fecha_vencimiento) FILTER (
                        WHERE i.fecha_vencimiento IS NOT NULL
                    ) AS proximo_vencimiento
                FROM public.inventario i
                JOIN public.producto p ON i.codigo_producto = p.codigo
                WHERE i.codigo_almacen = %s
                AND i.estado = true
                AND i.cantidad > 0
                GROUP BY i.codigo_producto, p.nombre
                ORDER BY p.nombre
            """, (codigo_almacen,))

            return cursor.fetchall()

    @staticmethod
    def register_entry(codigo_almacen, codigo_producto, cantidad, codigo_usuario, fecha_vencimiento=None):
        """
        Registrar entrada de producto al inventario.
        """
        if not codigo_almacen:
            raise ValueError('No se encontró el almacén.')

        if not codigo_producto:
            raise ValueError('Debe seleccionar un producto.')

        cantidad = Warehouse._to_int(cantidad, 'cantidad')

        if cantidad <= 0:
            raise ValueError('La cantidad debe ser mayor a cero.')

        if fecha_vencimiento == '':
            fecha_vencimiento = None

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    capacidad_actual,
                    capacidad_total
                FROM public.almacen
                WHERE codigo = %s
                FOR UPDATE
            """, (codigo_almacen,))

            warehouse = cursor.fetchone()

            if not warehouse:
                raise ValueError('El almacén no existe.')

            cursor.execute("""
                SELECT codigo, nombre
                FROM public.producto
                WHERE codigo = %s
                AND estado = true
            """, (codigo_producto,))

            product = cursor.fetchone()

            if not product:
                raise ValueError('El producto no existe o está inactivo.')

            capacidad_actual = warehouse['capacidad_actual'] or 0
            capacidad_total = warehouse['capacidad_total'] or 0

            if capacidad_total > 0 and capacidad_actual + cantidad > capacidad_total:
                raise ValueError(
                    'La entrada supera la capacidad total del almacén.'
                )

            cursor.execute("""
                INSERT INTO public.inventario (
                    codigo_producto,
                    codigo_almacen,
                    cantidad,
                    fecha_entrada,
                    fecha_vencimiento,
                    estado
                )
                VALUES (%s, %s, %s, CURRENT_DATE, %s, true)
                RETURNING
                    id,
                    codigo_producto,
                    codigo_almacen,
                    cantidad,
                    fecha_entrada,
                    fecha_vencimiento,
                    estado
            """, (
                codigo_producto,
                codigo_almacen,
                cantidad,
                fecha_vencimiento
            ))

            inventory = cursor.fetchone()

            cursor.execute("""
                UPDATE public.almacen
                SET capacidad_actual = capacidad_actual + %s
                WHERE codigo = %s
            """, (
                cantidad,
                codigo_almacen
            ))

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
            """, (
                codigo_usuario,
                'ENTRADA DE INVENTARIO',
                'inventario',
                str(inventory['id']),
                f'Entrada de {cantidad} unidades del producto {codigo_producto} al almacén {codigo_almacen}'
            ))

            return inventory

    @staticmethod
    def register_exit(codigo_almacen, codigo_producto, cantidad, codigo_usuario, motivo=None):
        """
        Registrar salida de producto del inventario.
        Descuenta por orden de entrada.
        """
        if not codigo_almacen:
            raise ValueError('No se encontró el almacén.')

        if not codigo_producto:
            raise ValueError('Debe seleccionar un producto.')

        cantidad = Warehouse._to_int(cantidad, 'cantidad')

        if cantidad <= 0:
            raise ValueError('La cantidad debe ser mayor a cero.')

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    nombre,
                    capacidad_actual,
                    capacidad_total
                FROM public.almacen
                WHERE codigo = %s
                FOR UPDATE
            """, (codigo_almacen,))

            warehouse = cursor.fetchone()

            if not warehouse:
                raise ValueError('El almacén no existe.')

            cursor.execute("""
                SELECT codigo, nombre
                FROM public.producto
                WHERE codigo = %s
                AND estado = true
            """, (codigo_producto,))

            product = cursor.fetchone()

            if not product:
                raise ValueError('El producto no existe o está inactivo.')

            cursor.execute("""
                SELECT COALESCE(SUM(cantidad), 0) AS stock_actual
                FROM public.inventario
                WHERE codigo_almacen = %s
                AND codigo_producto = %s
                AND estado = true
            """, (
                codigo_almacen,
                codigo_producto
            ))

            stock = cursor.fetchone()
            stock_actual = stock['stock_actual'] if stock else 0

            if stock_actual < cantidad:
                raise ValueError(
                    f'Stock insuficiente. Disponible: {stock_actual}, solicitado: {cantidad}.'
                )

            cursor.execute("""
                SELECT
                    id,
                    cantidad
                FROM public.inventario
                WHERE codigo_almacen = %s
                AND codigo_producto = %s
                AND estado = true
                AND cantidad > 0
                ORDER BY fecha_entrada ASC, id ASC
                FOR UPDATE
            """, (
                codigo_almacen,
                codigo_producto
            ))

            lots = cursor.fetchall()

            remaining = cantidad

            for lot in lots:
                if remaining <= 0:
                    break

                lot_quantity = lot['cantidad']

                if lot_quantity <= remaining:
                    cursor.execute("""
                        UPDATE public.inventario
                        SET cantidad = 0,
                            estado = false
                        WHERE id = %s
                    """, (lot['id'],))

                    remaining -= lot_quantity
                else:
                    cursor.execute("""
                        UPDATE public.inventario
                        SET cantidad = cantidad - %s
                        WHERE id = %s
                    """, (
                        remaining,
                        lot['id']
                    ))

                    remaining = 0

            cursor.execute("""
                UPDATE public.almacen
                SET capacidad_actual = GREATEST(capacidad_actual - %s, 0)
                WHERE codigo = %s
            """, (
                cantidad,
                codigo_almacen
            ))

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
            """, (
                codigo_usuario,
                'SALIDA DE INVENTARIO',
                'inventario',
                codigo_producto,
                f'Salida de {cantidad} unidades del producto {codigo_producto} del almacén {codigo_almacen}. Motivo: {motivo or "Sin motivo"}'
            ))

            return {
                'codigo_almacen': codigo_almacen,
                'codigo_producto': codigo_producto,
                'cantidad': cantidad
            }