from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.provider import Provider
from utils.decorators import login_required, permission_required

provider_bp = Blueprint('providers', __name__, url_prefix='/providers')


@provider_bp.route('/')
@login_required
@permission_required('provider_read')
def list_providers():
    """
    Listar proveedores.
    """
    providers = Provider.get_all()
    return render_template('providers/list.html', providers=providers)


@provider_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('provider_create')
def create_provider():
    """
    Crear proveedor.
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')

        if not nombre:
            flash('El nombre del proveedor es obligatorio', 'danger')
            return render_template('providers/create.html')

        if email and '@' not in email:
            flash('El correo electrónico no tiene un formato válido', 'danger')
            return render_template('providers/create.html')

        try:
            provider = Provider.create(
                nombre=nombre,
                descripcion=descripcion,
                direccion=direccion,
                telefono=telefono,
                email=email
            )

            if provider:
                flash(
                    f'Proveedor {provider["nombre"]} creado exitosamente con código {provider["codigo"]}',
                    'success'
                )
                return redirect(url_for('providers.list_providers'))
            else:
                flash('Error al crear el proveedor', 'danger')

        except Exception as e:
            flash(f'Error al crear proveedor: {str(e)}', 'danger')

    return render_template('providers/create.html')


@provider_bp.route('/edit/<codigo>', methods=['GET', 'POST'])
@login_required
@permission_required('provider_update')
def edit_provider(codigo):
    """
    Editar proveedor.
    """
    provider = Provider.find_by_codigo(codigo)

    if not provider:
        flash('Proveedor no encontrado', 'danger')
        return redirect(url_for('providers.list_providers'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')

        if not nombre:
            flash('El nombre del proveedor es obligatorio', 'danger')
            return render_template('providers/edit.html', provider=provider)

        if email and '@' not in email:
            flash('El correo electrónico no tiene un formato válido', 'danger')
            return render_template('providers/edit.html', provider=provider)

        try:
            updated_provider = Provider.update(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                direccion=direccion,
                telefono=telefono,
                email=email
            )

            if updated_provider:
                flash(f'Proveedor {updated_provider["nombre"]} actualizado exitosamente', 'success')
                return redirect(url_for('providers.list_providers'))
            else:
                flash('Error al actualizar el proveedor', 'danger')

        except Exception as e:
            flash(f'Error al actualizar proveedor: {str(e)}', 'danger')

    return render_template('providers/edit.html', provider=provider)


@provider_bp.route('/delete/<codigo>')
@login_required
@permission_required('provider_delete')
def delete_provider(codigo):
    """
    Eliminar proveedor.
    """
    try:
        result = Provider.delete(codigo)

        if result:
            flash('Proveedor eliminado exitosamente', 'success')
        else:
            flash('Proveedor no encontrado', 'danger')

    except ValueError as e:
        flash(str(e), 'danger')

    except Exception as e:
        flash(f'Error al eliminar proveedor: {str(e)}', 'danger')

    return redirect(url_for('providers.list_providers'))