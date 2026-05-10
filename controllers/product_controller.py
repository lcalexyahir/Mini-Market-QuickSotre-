from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.product import Product
from utils.decorators import login_required, permission_required

product_bp = Blueprint('products', __name__, url_prefix='/products')

@product_bp.route('/')
@login_required
@permission_required('product_read')
def list_products():
    """Listar productos"""
    products = Product.get_all()
    return render_template('products/list.html', products=products)

@product_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('product_create')
def create_product():
    """Crear producto"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))

        if not name or price <= 0 or stock < 0:
            flash('Todos los campos son obligatorios y deben ser válidos', 'danger')
            return render_template('products/create.html')

        product = Product.create(name, price, stock)
        if product:
            flash(f'Producto {product["nombre"]} creado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
        else:
            flash('Error al crear el producto', 'danger')

    return render_template('products/create.html')

@product_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@permission_required('product_update')
def edit_product(product_id):
    """Editar producto"""
    product = Product.find_by_id(product_id)
    if not product:
        flash('Producto no encontrado', 'danger')
        return redirect(url_for('products.list_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))

        updated_product = Product.update(product_id, name, price, stock)
        if updated_product:
            flash(f'Producto {updated_product["nombre"]} actualizado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
        else:
            flash('Error al actualizar el producto', 'danger')

    return render_template('products/edit.html', product=product)

@product_bp.route('/delete/<int:product_id>')
@login_required
@permission_required('product_delete')
def delete_product(product_id):
    """Eliminar producto"""
    result = Product.delete(product_id)
    if result:
        flash('Producto eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar el producto', 'danger')
    
    return redirect(url_for('products.list_products'))