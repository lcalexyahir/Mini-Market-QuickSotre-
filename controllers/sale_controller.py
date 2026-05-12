from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.sale import Sale
from utils.decorators import login_required, permission_required

sale_bp = Blueprint('sales', __name__, url_prefix='/sales')


@sale_bp.route('/')
@login_required
@permission_required('sale_read')
def list_sales():
    """
    Listar ventas registradas.
    """
    sales = Sale.get_all()

    return render_template(
        'sales/list.html',
        sales=sales
    )


@sale_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('sale_create')
def create_sale():
    """
    Registrar nueva venta.
    """
    clients = Sale.get_clients_for_sale()
    products = Sale.get_products_for_sale()
    payment_types = Sale.get_payment_types()

    if request.method == 'POST':
        id_cliente = request.form.get('id_cliente')
        id_tipo_pago = request.form.get('id_tipo_pago')
        referencia_externa = request.form.get('referencia_externa')

        product_codes = request.form.getlist('codigo_producto[]')
        quantities = request.form.getlist('cantidad[]')

        items = []

        for codigo_producto, cantidad in zip(product_codes, quantities):
            if codigo_producto and cantidad:
                items.append({
                    'codigo_producto': codigo_producto,
                    'cantidad': cantidad
                })

        try:
            result = Sale.create_sale(
                id_cliente=id_cliente,
                codigo_usuario=session.get('user_id'),
                id_tipo_pago=id_tipo_pago,
                items=items,
                referencia_externa=referencia_externa
            )

            invoice_code = result['invoice']['codigo']

            flash(f'Venta {invoice_code} registrada correctamente', 'success')
            return redirect(url_for('sales.detail_sale', codigo=invoice_code))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            flash(f'Error al registrar la venta: {str(e)}', 'danger')

    return render_template(
        'sales/create.html',
        clients=clients,
        products=products,
        payment_types=payment_types
    )


@sale_bp.route('/detail/<codigo>')
@login_required
@permission_required('sale_detail')
def detail_sale(codigo):
    """
    Ver detalle de una venta.
    """
    sale = Sale.find_by_code(codigo)

    if not sale:
        flash('Venta no encontrada', 'danger')
        return redirect(url_for('sales.list_sales'))

    details = Sale.get_details(codigo)

    return render_template(
        'sales/detail.html',
        sale=sale,
        details=details
    )


@sale_bp.route('/cancel/<codigo>')
@login_required
@permission_required('sale_cancel')
def cancel_sale(codigo):
    """
    Anular venta.
    """
    try:
        result = Sale.cancel_sale(
            codigo_factura=codigo,
            codigo_usuario=session.get('user_id')
        )

        if result:
            flash(f'Venta {codigo} anulada correctamente', 'success')
        else:
            flash('La venta no existe o ya fue anulada', 'warning')

    except Exception as e:
        flash(f'Error al anular la venta: {str(e)}', 'danger')

    return redirect(url_for('sales.list_sales'))