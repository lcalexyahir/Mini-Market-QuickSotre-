from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.cash import Cash
from utils.decorators import login_required, permission_required


cash_bp = Blueprint('cash', __name__, url_prefix='/cash')


@cash_bp.route('/')
@login_required
@permission_required('cash_read')
def list_cash():
    """
    Listar cajas registradas.
    """
    codigo_usuario = session.get('user_id')

    cash_registers = Cash.get_all()
    open_cash = Cash.get_open_cash(codigo_usuario)

    return render_template(
        'cash/list.html',
        cash_registers=cash_registers,
        open_cash=open_cash
    )


@cash_bp.route('/open', methods=['GET', 'POST'])
@login_required
@permission_required('cash_open')
def open_cash():
    """
    Abrir caja.
    """
    codigo_usuario = session.get('user_id')

    existing_cash = Cash.get_open_cash(codigo_usuario)

    if existing_cash:
        flash('Ya tienes una caja abierta. Debes cerrarla antes de abrir otra.', 'warning')
        return redirect(url_for('cash.detail_cash', codigo=existing_cash['codigo']))

    if request.method == 'POST':
        monto_inicial = request.form.get('monto_inicial')
        observacion_apertura = request.form.get('observacion_apertura')

        if monto_inicial is None or monto_inicial == '':
            flash('Debe ingresar el monto inicial.', 'danger')
            return render_template('cash/open.html')

        try:
            cash = Cash.open_cash(
                codigo_usuario=codigo_usuario,
                monto_inicial=monto_inicial,
                observacion_apertura=observacion_apertura
            )

            flash(f'Caja {cash["codigo"]} abierta correctamente.', 'success')
            return redirect(url_for('cash.detail_cash', codigo=cash['codigo']))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            flash(f'Error al abrir caja: {str(e)}', 'danger')

    return render_template('cash/open.html')


@cash_bp.route('/detail/<codigo>')
@login_required
@permission_required('cash_detail')
def detail_cash(codigo):
    """
    Ver detalle de caja.
    """
    cash = Cash.find_by_code(codigo)

    if not cash:
        flash('Caja no encontrada.', 'danger')
        return redirect(url_for('cash.list_cash'))

    summary = Cash.get_sales_summary(cash)

    totals = Cash.calculate_totals(
        summary=summary,
        monto_inicial=cash['monto_inicial'],
        monto_final=cash['monto_final']
    )

    return render_template(
        'cash/detail.html',
        cash=cash,
        summary=summary,
        totals=totals
    )


@cash_bp.route('/close/<codigo>', methods=['GET', 'POST'])
@login_required
@permission_required('cash_close')
def close_cash(codigo):
    """
    Cerrar caja.
    """
    cash = Cash.find_by_code(codigo)

    if not cash:
        flash('Caja no encontrada.', 'danger')
        return redirect(url_for('cash.list_cash'))

    if cash['estado'] != 'abierta':
        flash('Esta caja ya está cerrada.', 'warning')
        return redirect(url_for('cash.detail_cash', codigo=codigo))

    if cash['codigo_usuario'] != session.get('user_id') and session.get('rol') != 'admin':
        flash('Solo puedes cerrar tu propia caja.', 'danger')
        return redirect(url_for('cash.list_cash'))

    summary = Cash.get_sales_summary(cash)

    totals = Cash.calculate_totals(
        summary=summary,
        monto_inicial=cash['monto_inicial']
    )

    if request.method == 'POST':
        monto_final = request.form.get('monto_final')
        observacion_cierre = request.form.get('observacion_cierre')

        if monto_final is None or monto_final == '':
            flash('Debe ingresar el monto final.', 'danger')
            return render_template(
                'cash/close.html',
                cash=cash,
                summary=summary,
                totals=totals
            )

        try:
            is_admin = session.get('rol') == 'admin'

            closed_cash = Cash.close_cash(
                codigo_caja=codigo,
                codigo_usuario=session.get('user_id'),
                monto_final=monto_final,
                observacion_cierre=observacion_cierre,
                is_admin=is_admin
            )

            flash(f'Caja {closed_cash["codigo"]} cerrada correctamente.', 'success')
            return redirect(url_for('cash.detail_cash', codigo=closed_cash['codigo']))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            flash(f'Error al cerrar caja: {str(e)}', 'danger')

    return render_template(
        'cash/close.html',
        cash=cash,
        summary=summary,
        totals=totals
    )