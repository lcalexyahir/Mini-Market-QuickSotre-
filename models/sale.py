from database.connection import db
from decimal import Decimal


class Sale:

    @staticmethod
    def count_all():
        """
        Contar ventas activas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.factura
                WHERE estado = true
            """)

            result = cursor.fetchone()
            return result['total'] if result else 0

    @staticmethod
    def get_payment_types():
        """
        Obtener tipos de pago activos.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, descripcion, activo
                FROM public.tipo_pago
                WHERE activo = true
                ORDER BY id
            """)

            return cursor.fetchall()

    @staticmethod
    def get_clients_for_sale():
        """
        Obtener clientes disponibles para ventas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, ci, nombre, correo_electronico, telefono
                FROM public.cliente
                ORDER BY nombre
            """)

            return cursor.fetchall()

    @staticmethod
    def get_products_for_sale():
        """
        Obtener productos activos disponibles para venta.
        No descuenta inventario todavía porque CU08 Almacén se hará después.
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
    def _generate_invoice_code(cursor):
        """
        Generar código automático de factura.
        Ejemplo: FAC001, FAC002, FAC003.
        """
        cursor.execute("""
            SELECT codigo
            FROM public.factura
            WHERE codigo ~ '^FAC[0-9]+$'
            ORDER BY CAST(SUBSTRING(codigo FROM 4) AS INTEGER) DESC
            LIMIT 1
        """)

        last_invoice = cursor.fetchone()

        if not last_invoice:
            return 'FAC001'

        last_code = last_invoice['codigo']
        last_number = int(last_code.replace('FAC', ''))
        new_number = last_number + 1

        return f'FAC{new_number:03d}'

    @staticmethod
    def _get_product(cursor, codigo_producto):
        """
        Obtener producto activo por código.
        """
        cursor.execute("""
            SELECT
                codigo,
                nombre,
                precio_venta,
                estado
            FROM public.producto
            WHERE codigo = %s
            AND estado = true
        """, (codigo_producto,))

        return cursor.fetchone()

    @staticmethod
    def create_sale(id_cliente, codigo_usuario, id_tipo_pago, items, referencia_externa=None):
        """
        Registrar una venta completa:
        - factura
        - detalle_factura
        - pago
        - historial

        items debe tener esta estructura:
        [
            {
                'codigo_producto': 'PROD001',
                'cantidad': 2
            }
        ]
        """

        if not id_cliente:
            raise ValueError('Debe seleccionar un cliente.')

        if not codigo_usuario:
            raise ValueError('No se encontró el usuario de la sesión.')

        if not id_tipo_pago:
            raise ValueError('Debe seleccionar un tipo de pago.')

        if not items:
            raise ValueError('Debe agregar al menos un producto a la venta.')

        with db.get_cursor() as cursor:

            # Validar cliente
            cursor.execute("""
                SELECT id, nombre
                FROM public.cliente
                WHERE id = %s
            """, (id_cliente,))

            client = cursor.fetchone()

            if not client:
                raise ValueError('El cliente seleccionado no existe.')

            # Validar tipo de pago
            cursor.execute("""
                SELECT id, nombre
                FROM public.tipo_pago
                WHERE id = %s
                AND activo = true
            """, (id_tipo_pago,))

            payment_type = cursor.fetchone()

            if not payment_type:
                raise ValueError('El tipo de pago seleccionado no existe o está inactivo.')

            codigo_factura = Sale._generate_invoice_code(cursor)

            detalles = []
            monto_total = Decimal('0.00')

            for item in items:
                codigo_producto = item.get('codigo_producto')
                cantidad = item.get('cantidad')

                if not codigo_producto:
                    raise ValueError('Hay un producto sin código.')

                try:
                    cantidad = int(cantidad)
                except Exception:
                    raise ValueError('La cantidad debe ser un número entero.')

                if cantidad <= 0:
                    raise ValueError('La cantidad debe ser mayor a cero.')

                product = Sale._get_product(cursor, codigo_producto)

                if not product:
                    raise ValueError(f'El producto {codigo_producto} no existe o está inactivo.')

                precio_unitario = Decimal(str(product['precio_venta']))
                subtotal = precio_unitario * Decimal(cantidad)

                detalles.append({
                    'codigo_producto': product['codigo'],
                    'nombre_producto': product['nombre'],
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal
                })

                monto_total += subtotal

            if monto_total <= 0:
                raise ValueError('El monto total de la venta debe ser mayor a cero.')

            monto_final = monto_total

            # Insertar factura
            cursor.execute("""
                INSERT INTO public.factura (
                    codigo,
                    id_cliente,
                    codigo_usuario,
                    id_tipo_pago,
                    codigo_descuento,
                    monto_total,
                    monto_final,
                    pagado,
                    estado,
                    codigo_pedido
                )
                VALUES (%s, %s, %s, %s, NULL, %s, %s, true, true, NULL)
                RETURNING
                    codigo,
                    fecha_hora,
                    id_cliente,
                    codigo_usuario,
                    id_tipo_pago,
                    monto_total,
                    monto_final,
                    pagado,
                    estado
            """, (
                codigo_factura,
                id_cliente,
                codigo_usuario,
                id_tipo_pago,
                monto_total,
                monto_final
            ))

            invoice = cursor.fetchone()

            # Insertar detalle de factura
            for detail in detalles:
                cursor.execute("""
                    INSERT INTO public.detalle_factura (
                        codigo_factura,
                        codigo_producto,
                        cantidad,
                        precio_unitario,
                        subtotal
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    codigo_factura,
                    detail['codigo_producto'],
                    detail['cantidad'],
                    detail['precio_unitario'],
                    detail['subtotal']
                ))

            # Insertar pago
            cursor.execute("""
                INSERT INTO public.pago (
                    codigo_factura,
                    id_tipo_pago,
                    monto_pagado,
                    codigo_usuario,
                    referencia_externa
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, codigo_factura, monto_pagado
            """, (
                codigo_factura,
                id_tipo_pago,
                monto_final,
                codigo_usuario,
                referencia_externa
            ))

            payment = cursor.fetchone()

            # Registrar historial
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
                'REGISTRO DE VENTA',
                'factura',
                codigo_factura,
                f'Venta registrada por Bs {monto_final}'
            ))

            return {
                'invoice': invoice,
                'details': detalles,
                'payment': payment
            }

    @staticmethod
    def get_all():
        """
        Listar ventas registradas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    f.codigo,
                    f.fecha_hora,
                    f.monto_total,
                    f.monto_final,
                    f.pagado,
                    f.estado,
                    c.nombre AS cliente,
                    c.ci AS cliente_ci,
                    u.nombre AS usuario,
                    tp.nombre AS tipo_pago
                FROM public.factura f
                JOIN public.cliente c ON f.id_cliente = c.id
                JOIN public.usuario u ON f.codigo_usuario = u.codigo
                JOIN public.tipo_pago tp ON f.id_tipo_pago = tp.id
                ORDER BY f.fecha_hora DESC
            """)

            return cursor.fetchall()

    @staticmethod
    def find_by_code(codigo_factura):
        """
        Buscar factura por código.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    f.codigo,
                    f.fecha_hora,
                    f.id_cliente,
                    f.codigo_usuario,
                    f.id_tipo_pago,
                    f.monto_total,
                    f.monto_final,
                    f.pagado,
                    f.estado,
                    c.nombre AS cliente,
                    c.ci AS cliente_ci,
                    c.telefono AS cliente_telefono,
                    c.correo_electronico AS cliente_email,
                    u.nombre AS usuario,
                    tp.nombre AS tipo_pago
                FROM public.factura f
                JOIN public.cliente c ON f.id_cliente = c.id
                JOIN public.usuario u ON f.codigo_usuario = u.codigo
                JOIN public.tipo_pago tp ON f.id_tipo_pago = tp.id
                WHERE f.codigo = %s
            """, (codigo_factura,))

            return cursor.fetchone()

    @staticmethod
    def get_details(codigo_factura):
        """
        Obtener detalle de productos de una factura.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    df.id,
                    df.codigo_factura,
                    df.codigo_producto,
                    p.nombre AS producto,
                    df.cantidad,
                    df.precio_unitario,
                    df.subtotal
                FROM public.detalle_factura df
                JOIN public.producto p ON df.codigo_producto = p.codigo
                WHERE df.codigo_factura = %s
                ORDER BY df.id
            """, (codigo_factura,))

            return cursor.fetchall()

    @staticmethod
    def cancel_sale(codigo_factura, codigo_usuario):
        """
        Anular venta.
        No elimina físicamente la factura.
        Solo cambia estado y pagado.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE public.factura
                SET estado = false,
                    pagado = false
                WHERE codigo = %s
                AND estado = true
                RETURNING codigo, monto_final
            """, (codigo_factura,))

            result = cursor.fetchone()

            if result:
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
                    'ANULACION DE VENTA',
                    'factura',
                    codigo_factura,
                    f'Venta anulada por Bs {result["monto_final"]}'
                ))

            return result