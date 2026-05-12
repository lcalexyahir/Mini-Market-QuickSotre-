from database.connection import db
from decimal import Decimal


class Cash:

    @staticmethod
    def _to_decimal(value):
        """
        Convertir valores a Decimal de forma segura.
        """
        if value is None:
            return Decimal('0.00')

        return Decimal(str(value))

    @staticmethod
    def _generate_cash_code(cursor):
        """
        Generar código automático de caja.
        Ejemplo: CJA001, CJA002, CJA003.
        """
        cursor.execute("""
            SELECT codigo
            FROM public.caja
            WHERE codigo ~ '^CJA[0-9]+$'
            ORDER BY CAST(SUBSTRING(codigo FROM 4) AS INTEGER) DESC
            LIMIT 1
        """)

        last_cash = cursor.fetchone()

        if not last_cash:
            return 'CJA001'

        last_code = last_cash['codigo']
        last_number = int(last_code.replace('CJA', ''))
        new_number = last_number + 1

        return f'CJA{new_number:03d}'

    @staticmethod
    def count_all():
        """
        Contar todas las cajas registradas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.caja
            """)

            result = cursor.fetchone()
            return result['total'] if result else 0

    @staticmethod
    def count_open():
        """
        Contar cajas abiertas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM public.caja
                WHERE estado = 'abierta'
            """)

            result = cursor.fetchone()
            return result['total'] if result else 0

    @staticmethod
    def get_open_cash(codigo_usuario):
        """
        Obtener caja abierta del usuario actual.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    codigo_usuario,
                    fecha_apertura,
                    fecha_cierre,
                    monto_inicial,
                    monto_final,
                    total_ventas,
                    total_efectivo,
                    total_qr,
                    total_tarjeta,
                    total_transferencia,
                    diferencia,
                    estado,
                    observacion_apertura,
                    observacion_cierre
                FROM public.caja
                WHERE codigo_usuario = %s
                AND estado = 'abierta'
                ORDER BY fecha_apertura DESC
                LIMIT 1
            """, (codigo_usuario,))

            return cursor.fetchone()

    @staticmethod
    def get_all(limit=100):
        """
        Listar cajas registradas.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.codigo,
                    c.codigo_usuario,
                    u.nombre AS usuario,
                    u.rol,
                    c.fecha_apertura,
                    c.fecha_cierre,
                    c.monto_inicial,
                    c.monto_final,
                    c.total_ventas,
                    c.total_efectivo,
                    c.total_qr,
                    c.total_tarjeta,
                    c.total_transferencia,
                    c.diferencia,
                    c.estado,
                    c.observacion_apertura,
                    c.observacion_cierre
                FROM public.caja c
                JOIN public.usuario u ON c.codigo_usuario = u.codigo
                ORDER BY c.fecha_apertura DESC
                LIMIT %s
            """, (limit,))

            return cursor.fetchall()

    @staticmethod
    def find_by_code(codigo):
        """
        Buscar caja por código.
        """
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.codigo,
                    c.codigo_usuario,
                    u.nombre AS usuario,
                    u.rol,
                    c.fecha_apertura,
                    c.fecha_cierre,
                    c.monto_inicial,
                    c.monto_final,
                    c.total_ventas,
                    c.total_efectivo,
                    c.total_qr,
                    c.total_tarjeta,
                    c.total_transferencia,
                    c.diferencia,
                    c.estado,
                    c.observacion_apertura,
                    c.observacion_cierre
                FROM public.caja c
                JOIN public.usuario u ON c.codigo_usuario = u.codigo
                WHERE c.codigo = %s
            """, (codigo,))

            return cursor.fetchone()

    @staticmethod
    def open_cash(codigo_usuario, monto_inicial, observacion_apertura=None):
        """
        Abrir caja para el usuario actual.
        Solo puede existir una caja abierta por usuario.
        """
        monto_inicial = Cash._to_decimal(monto_inicial)

        if monto_inicial < 0:
            raise ValueError('El monto inicial no puede ser negativo.')

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT codigo
                FROM public.caja
                WHERE codigo_usuario = %s
                AND estado = 'abierta'
                LIMIT 1
            """, (codigo_usuario,))

            existing = cursor.fetchone()

            if existing:
                raise ValueError('Ya tienes una caja abierta. Debes cerrarla antes de abrir otra.')

            codigo_caja = Cash._generate_cash_code(cursor)

            cursor.execute("""
                INSERT INTO public.caja (
                    codigo,
                    codigo_usuario,
                    monto_inicial,
                    estado,
                    observacion_apertura
                )
                VALUES (%s, %s, %s, 'abierta', %s)
                RETURNING
                    codigo,
                    codigo_usuario,
                    fecha_apertura,
                    monto_inicial,
                    estado
            """, (
                codigo_caja,
                codigo_usuario,
                monto_inicial,
                observacion_apertura
            ))

            cash = cursor.fetchone()

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
                'APERTURA DE CAJA',
                'caja',
                codigo_caja,
                f'Caja abierta con monto inicial Bs {monto_inicial}'
            ))

            return cash

    @staticmethod
    def _get_sales_summary_by_range(cursor, codigo_usuario, fecha_inicio, fecha_fin=None):
        """
        Obtener resumen de ventas y pagos entre apertura y cierre de caja.
        Si fecha_fin es None, calcula hasta el momento actual.
        """
        if fecha_fin:
            date_condition = """
                p.fecha_pago >= %s
                AND p.fecha_pago <= %s
            """
            params_general = (fecha_inicio, fecha_fin, codigo_usuario)
            params_payment = (fecha_inicio, fecha_fin, codigo_usuario)
        else:
            date_condition = """
                p.fecha_pago >= %s
            """
            params_general = (fecha_inicio, codigo_usuario)
            params_payment = (fecha_inicio, codigo_usuario)

        cursor.execute(f"""
            SELECT
                COUNT(DISTINCT f.codigo) AS cantidad_ventas,
                COALESCE(SUM(p.monto_pagado), 0) AS total_ventas
            FROM public.pago p
            JOIN public.factura f ON p.codigo_factura = f.codigo
            WHERE {date_condition}
            AND p.codigo_usuario = %s
            AND f.estado = true
        """, params_general)

        general = cursor.fetchone()

        cursor.execute(f"""
            SELECT
                tp.nombre AS tipo_pago,
                COALESCE(SUM(p.monto_pagado), 0) AS total
            FROM public.pago p
            JOIN public.factura f ON p.codigo_factura = f.codigo
            JOIN public.tipo_pago tp ON p.id_tipo_pago = tp.id
            WHERE {date_condition}
            AND p.codigo_usuario = %s
            AND f.estado = true
            GROUP BY tp.nombre
            ORDER BY tp.nombre
        """, params_payment)

        by_payment = cursor.fetchall()

        return {
            'general': general,
            'by_payment': by_payment
        }

    @staticmethod
    def get_sales_summary(cash):
        """
        Obtener resumen de ventas de una caja.
        """
        with db.get_cursor() as cursor:
            return Cash._get_sales_summary_by_range(
                cursor=cursor,
                codigo_usuario=cash['codigo_usuario'],
                fecha_inicio=cash['fecha_apertura'],
                fecha_fin=cash['fecha_cierre']
            )

    @staticmethod
    def calculate_totals(summary, monto_inicial=0, monto_final=None):
        """
        Calcular totales por tipo de pago y diferencia de caja.

        La diferencia se calcula así:
        diferencia = monto_final - (monto_inicial + total_efectivo)

        QR, tarjeta y transferencia se registran como ventas,
        pero no se comparan con dinero físico en caja.
        """
        monto_inicial = Cash._to_decimal(monto_inicial)
        monto_final_decimal = Cash._to_decimal(monto_final) if monto_final is not None else None

        total_ventas = Cash._to_decimal(summary['general']['total_ventas'])
        cantidad_ventas = summary['general']['cantidad_ventas'] or 0

        total_efectivo = Decimal('0.00')
        total_qr = Decimal('0.00')
        total_tarjeta = Decimal('0.00')
        total_transferencia = Decimal('0.00')
        total_otros = Decimal('0.00')

        for item in summary['by_payment']:
            tipo_pago = (item['tipo_pago'] or '').lower()
            total = Cash._to_decimal(item['total'])

            if 'efectivo' in tipo_pago:
                total_efectivo += total
            elif 'qr' in tipo_pago:
                total_qr += total
            elif 'tarjeta' in tipo_pago:
                total_tarjeta += total
            elif 'transferencia' in tipo_pago:
                total_transferencia += total
            else:
                total_otros += total

        efectivo_esperado = monto_inicial + total_efectivo

        diferencia = None

        if monto_final_decimal is not None:
            diferencia = monto_final_decimal - efectivo_esperado

        return {
            'cantidad_ventas': cantidad_ventas,
            'monto_inicial': monto_inicial,
            'total_ventas': total_ventas,
            'total_efectivo': total_efectivo,
            'total_qr': total_qr,
            'total_tarjeta': total_tarjeta,
            'total_transferencia': total_transferencia,
            'total_otros': total_otros,
            'efectivo_esperado': efectivo_esperado,
            'monto_final': monto_final_decimal,
            'diferencia': diferencia
        }

    @staticmethod
    def close_cash(codigo_caja, codigo_usuario, monto_final, observacion_cierre=None, is_admin=False):
        """
        Cerrar caja.
        Calcula ventas, pagos por tipo, efectivo esperado y diferencia.
        """
        monto_final = Cash._to_decimal(monto_final)

        if monto_final < 0:
            raise ValueError('El monto final no puede ser negativo.')

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    codigo,
                    codigo_usuario,
                    fecha_apertura,
                    fecha_cierre,
                    monto_inicial,
                    estado
                FROM public.caja
                WHERE codigo = %s
                FOR UPDATE
            """, (codigo_caja,))

            cash = cursor.fetchone()

            if not cash:
                raise ValueError('La caja no existe.')

            if cash['estado'] != 'abierta':
                raise ValueError('La caja ya está cerrada.')

            if cash['codigo_usuario'] != codigo_usuario and not is_admin:
                raise ValueError('Solo puedes cerrar tu propia caja.')

            summary = Cash._get_sales_summary_by_range(
                cursor=cursor,
                codigo_usuario=cash['codigo_usuario'],
                fecha_inicio=cash['fecha_apertura'],
                fecha_fin=None
            )

            totals = Cash.calculate_totals(
                summary=summary,
                monto_inicial=cash['monto_inicial'],
                monto_final=monto_final
            )

            cursor.execute("""
                UPDATE public.caja
                SET
                    fecha_cierre = CURRENT_TIMESTAMP,
                    monto_final = %s,
                    total_ventas = %s,
                    total_efectivo = %s,
                    total_qr = %s,
                    total_tarjeta = %s,
                    total_transferencia = %s,
                    diferencia = %s,
                    estado = 'cerrada',
                    observacion_cierre = %s
                WHERE codigo = %s
                RETURNING
                    codigo,
                    codigo_usuario,
                    fecha_apertura,
                    fecha_cierre,
                    monto_inicial,
                    monto_final,
                    total_ventas,
                    total_efectivo,
                    total_qr,
                    total_tarjeta,
                    total_transferencia,
                    diferencia,
                    estado
            """, (
                totals['monto_final'],
                totals['total_ventas'],
                totals['total_efectivo'],
                totals['total_qr'],
                totals['total_tarjeta'],
                totals['total_transferencia'],
                totals['diferencia'],
                observacion_cierre,
                codigo_caja
            ))

            closed_cash = cursor.fetchone()

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
                'CIERRE DE CAJA',
                'caja',
                codigo_caja,
                f'Caja cerrada. Total ventas Bs {totals["total_ventas"]}, diferencia Bs {totals["diferencia"]}'
            ))

            return closed_cash