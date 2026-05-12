from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.warehouse import Warehouse
from models.permission import Permission
from utils.decorators import login_required, permission_required


warehouse_bp = Blueprint('warehouses', __name__, url_prefix='/warehouses')


@warehouse_bp.route('/')
@login_required
@permission_required('warehouse_read')
def list_warehouses():
    """
    Listar almacenes.
    """
    warehouses = Warehouse.get_all()

    return render_template(
        'warehouses/list.html',
        warehouses=warehouses
    )


@warehouse_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('warehouse_create')
def create_warehouse():
    """
    Crear almacén.
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        capacidad_total = request.form.get('capacidad_total')

        try:
            warehouse = Warehouse.create(
                nombre=nombre,
                direccion=direccion,
                capacidad_total=capacidad_total
            )

            flash(f'Almacén {warehouse["codigo"]} creado correctamente.', 'success')
            return redirect(url_for('warehouses.list_warehouses'))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            flash(f'Error al crear almacén: {str(e)}', 'danger')

    return render_template('warehouses/create.html')


@warehouse_bp.route('/edit/<codigo>', methods=['GET', 'POST'])
@login_required
@permission_required('warehouse_update')
def edit_warehouse(codigo):
    """
    Editar almacén.
    """
    warehouse = Warehouse.find_by_code(codigo)

    if not warehouse:
        flash('Almacén no encontrado.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        capacidad_total = request.form.get('capacidad_total')

        try:
            updated_warehouse = Warehouse.update(
                codigo=codigo,
                nombre=nombre,
                direccion=direccion,
                capacidad_total=capacidad_total
            )

            flash(f'Almacén {updated_warehouse["codigo"]} actualizado correctamente.', 'success')
            return redirect(url_for('warehouses.list_warehouses'))

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            flash(f'Error al actualizar almacén: {str(e)}', 'danger')

    return render_template(
        'warehouses/edit.html',
        warehouse=warehouse
    )


@warehouse_bp.route('/delete/<codigo>')
@login_required
@permission_required('warehouse_delete')
def delete_warehouse(codigo):
    """
    Eliminar almacén.
    """
    try:
        result = Warehouse.delete(codigo)

        if result:
            flash('Almacén eliminado correctamente.', 'success')
        else:
            flash('Almacén no encontrado.', 'warning')

    except ValueError as e:
        flash(str(e), 'danger')

    except Exception as e:
        flash(f'Error al eliminar almacén: {str(e)}', 'danger')

    return redirect(url_for('warehouses.list_warehouses'))


@warehouse_bp.route('/detail/<codigo>')
@login_required
@permission_required('warehouse_detail')
def detail_warehouse(codigo):
    """
    Ver detalle e inventario de almacén.
    """
    warehouse = Warehouse.find_by_code(codigo)

    if not warehouse:
        flash('Almacén no encontrado.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))

    inventory = Warehouse.get_inventory_by_warehouse(codigo)
    products = Warehouse.get_products_for_inventory()

    codigo_usuario = session.get('user_id')

    permissions = {
        'can_entry': Permission.has_permission(codigo_usuario, 'warehouse_inventory_entry'),
        'can_exit': Permission.has_permission(codigo_usuario, 'warehouse_inventory_exit')
    }

    return render_template(
        'warehouses/detail.html',
        warehouse=warehouse,
        inventory=inventory,
        products=products,
        permissions=permissions
    )


@warehouse_bp.route('/entry/<codigo>', methods=['POST'])
@login_required
@permission_required('warehouse_inventory_entry')
def register_entry(codigo):
    """
    Registrar entrada de producto al almacén.
    """
    codigo_producto = request.form.get('codigo_producto')
    cantidad = request.form.get('cantidad')
    fecha_vencimiento = request.form.get('fecha_vencimiento')

    try:
        Warehouse.register_entry(
            codigo_almacen=codigo,
            codigo_producto=codigo_producto,
            cantidad=cantidad,
            codigo_usuario=session.get('user_id'),
            fecha_vencimiento=fecha_vencimiento
        )

        flash('Entrada de inventario registrada correctamente.', 'success')

    except ValueError as e:
        flash(str(e), 'danger')

    except Exception as e:
        flash(f'Error al registrar entrada: {str(e)}', 'danger')

    return redirect(url_for('warehouses.detail_warehouse', codigo=codigo))


@warehouse_bp.route('/exit/<codigo>', methods=['POST'])
@login_required
@permission_required('warehouse_inventory_exit')
def register_exit(codigo):
    """
    Registrar salida de producto del almacén.
    """
    codigo_producto = request.form.get('codigo_producto')
    cantidad = request.form.get('cantidad')
    motivo = request.form.get('motivo')

    try:
        Warehouse.register_exit(
            codigo_almacen=codigo,
            codigo_producto=codigo_producto,
            cantidad=cantidad,
            codigo_usuario=session.get('user_id'),
            motivo=motivo
        )

        flash('Salida de inventario registrada correctamente.', 'success')

    except ValueError as e:
        flash(str(e), 'danger')

    except Exception as e:
        flash(f'Error al registrar salida: {str(e)}', 'danger')

    return redirect(url_for('warehouses.detail_warehouse', codigo=codigo))