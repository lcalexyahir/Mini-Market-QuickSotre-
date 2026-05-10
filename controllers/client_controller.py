from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.client import Client
from utils.decorators import login_required, permission_required

client_bp = Blueprint('clients', __name__, url_prefix='/clients')


@client_bp.route('/')
@login_required
@permission_required('client_read')
def list_clients():
    """Listar clientes"""
    clients = Client.get_all()
    return render_template('clients/list.html', clients=clients)


@client_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('client_create')
def create_client():
    """Crear cliente"""
    if request.method == 'POST':
        # Obtener los datos del formulario
        document_id = request.form.get('ci')
        full_name = request.form.get('nombre')
        email = request.form.get('email')
        phone = request.form.get('telefono')
       
        # Validación de campos obligatorios
        if not all([document_id, full_name]):
            flash('Documento y nombre son requeridos', 'danger')
            return render_template('clients/create.html')
       
        # Verificar si ya existe un cliente con el mismo documento
        existing = Client.find_by_document(document_id)
        if existing:
            flash('Ya existe un cliente con ese documento', 'danger')
            return render_template('clients/create.html')
       
        # Crear el cliente
        client = Client.create(document_id, full_name, email, phone)  # Eliminamos 'address'
        if client:
            flash(f'Cliente {client["full_name"]} creado exitosamente', 'success')
            return redirect(url_for('clients.list_clients'))
        else:
            flash('Error al crear el cliente', 'danger')
   
    return render_template('clients/create.html')


@client_bp.route('/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
@permission_required('client_update')
def edit_client(client_id):
    """Editar cliente"""
    client = Client.find_by_id(client_id)
    if not client:
        flash('Cliente no encontrado', 'danger')
        return redirect(url_for('clients.list_clients'))
   
    if request.method == 'POST':
        # Obtener los datos del formulario
        full_name = request.form.get('nombre')
        email = request.form.get('email')
        phone = request.form.get('telefono')
        is_active = request.form.get('is_active') == 'on'
       
        # Actualizar el cliente
        updated_client = Client.update(
            client_id,
            full_name=full_name,
            email=email,
            phone=phone,
            is_active=is_active
        )
       
        if updated_client:
            flash(f'Cliente {updated_client["full_name"]} actualizado exitosamente', 'success')
            return redirect(url_for('clients.list_clients'))
        else:
            flash('Error al actualizar el cliente', 'danger')
   
    return render_template('clients/edit.html', client=client)


@client_bp.route('/delete/<int:client_id>')
@login_required
@permission_required('client_delete')
def delete_client(client_id):
    """Eliminar cliente"""
    result = Client.delete(client_id)
    if result:
        flash('Cliente eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar el cliente', 'danger')
   
    return redirect(url_for('clients.list_clients'))


@client_bp.route('/search')
@login_required
def search_clients():
    """API: Buscar clientes (para autocomplete)"""
    term = request.args.get('term', '')
    if len(term) < 2:
        return jsonify([])
   
    clients = Client.search(term)
    return jsonify([{
        'id': c['id'],
        'document_id': c['document_id'],
        'full_name': c['full_name'],
        'email': c['email'],
        'phone': c['phone']
    } for c in clients])