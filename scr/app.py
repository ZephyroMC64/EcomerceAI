from flask import Flask, render_template, request,redirect,url_for,flash,session
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from models import db, Producto, Categoria, Usuario
from models.usuario import Direccion
from models.factura import Pedido, TransaccionPago,DetallePedido
from models.asociaciones import producto_categoria
from sqlalchemy import func
from datetime import datetime
import os
import random
from recommender import ProductRecommender
recommender = None
app = Flask(__name__)
app.config.from_object(Config)
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'img', 'productos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/catalogo')
def catalogo():

    q = request.args.get('q', default='')
    category_id = request.args.get('category_id')

    productos_query = Producto.query.filter_by(activo=True)

    if q:
        productos_query = productos_query.filter(Producto.nombre.ilike(f"%{q}%"))

    if category_id:
        try:
            cat_id = int(category_id)
            productos_query = productos_query.join(Producto.categorias).filter(Categoria.id == cat_id)
        except ValueError:
            pass

    productos = productos_query.all()

    categorias_con_conteo = (
        db.session.query(
            Categoria.id,
            Categoria.nombre,
            func.count(Producto.id).label('total_productos')
        )
        .outerjoin(producto_categoria, Categoria.id == producto_categoria.c.categoria_id)
        .outerjoin(Producto, producto_categoria.c.producto_id == Producto.id)
        .group_by(Categoria.id, Categoria.nombre)
        .all()
    )

    categorias = [
        {'id': c_id, 'nombre': c_nombre, 'total_productos': count}
        for c_id, c_nombre, count in categorias_con_conteo
    ]

    return render_template(
        'catalogo.html',
        productos=productos,
        categorias=categorias,
        current_query=q
    )

@app.route('/producto/<int:producto_id>')
def detalle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    # Recomendaciones por similitud
    similares_ids = recommender.recomendar(producto_id, top_n=4) if recommender else []
    productos_similares = Producto.query.filter(Producto.id.in_(similares_ids)).all()

    return render_template("detalle_producto.html",
                           producto=producto,
                           similares=productos_similares)





@app.route('/carrito/actualizar/<int:producto_id>', methods=['POST'])
def actualizar_carrito(producto_id):
    nueva_cantidad = int(request.form.get("cantidad", 1))
    carrito = session.get("carrito", {})

    if str(producto_id) in carrito:
        carrito[str(producto_id)]["cantidad"] = nueva_cantidad

    session.modified = True
    return redirect(url_for("carrito"))


@app.route('/carrito/eliminar/<int:producto_id>')
def eliminar_carrito(producto_id):
    carrito = session.get("carrito", {})
    carrito.pop(str(producto_id), None)
    session.modified = True
    return redirect(url_for("carrito"))


@app.route('/carrito/vaciar')
def vaciar_carrito():
    session.pop("carrito", None)
    return redirect(url_for("carrito"))

@app.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    cantidad = int(request.form.get('quantity', 1))

    producto = Producto.query.get_or_404(producto_id)

    # Si no hay carrito, lo creamos
    if 'carrito' not in session:
        session['carrito'] = {}

    carrito = session['carrito']

    # Si el producto ya existe en el carrito, sumamos la cantidad
    if str(producto_id) in carrito:
        carrito[str(producto_id)]['cantidad'] += cantidad
    else:
        carrito[str(producto_id)] = {
            'id': producto_id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'cantidad': cantidad
        }

    session.modified = True
    flash("Producto agregado al carrito 🛒", "success")

    return redirect(url_for('detalle_producto', producto_id=producto_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Buscar usuario por email
        user = Usuario.query.filter_by(email=email).first()

        if not user:
            flash("El correo no está registrado.", "error")
            return redirect(url_for('login'))

        # Comparar hash de contraseña
        if not check_password_hash(user.contrasena_hash, password):
            flash("Contraseña incorrecta.", "error")
            return redirect(url_for('login'))

        # Guardar datos en sesión
        session['user_id'] = user.id
        session['user_name'] = user.nombre
        session['user_role'] = user.rol

        flash("Inicio de sesión exitoso.", "success")
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/carrito')
def carrito():
    carrito = session.get('carrito', {})
    return render_template('carrito.html', carrito=carrito)

@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        flash("Debes iniciar sesión para continuar", "warning")
        return redirect(url_for("login"))

    carrito = session.get("carrito", {})
    if not carrito:
        flash("Tu carrito está vacío", "warning")
        return redirect(url_for("carrito"))

    total = sum(item["precio"] * item["cantidad"] for item in carrito.values())

    direcciones = Direccion.query.filter_by(usuario_id=session["user_id"]).all()

    return render_template("checkout.html", 
                           carrito=carrito, 
                           total=total,
                           direcciones=direcciones)

@app.route("/checkout/procesar", methods=["POST"])
def procesar_checkout():
    if "user_id" not in session:
        flash("Debes iniciar sesión", "danger")
        return redirect(url_for("login"))

    carrito = session.get("carrito", {})
    if not carrito:
        flash("El carrito está vacío", "warning")
        return redirect(url_for("carrito"))

    metodo_pago = request.form["metodo_pago"]
    proveedor_logistico = request.form["proveedor_logistico"]
    direccion_id = request.form["direccion_envio"]

    total = sum(item["precio"] * item["cantidad"] for item in carrito.values())

    # 1. Crear el pedido
    pedido = Pedido(
        cliente_id=session["user_id"],
        fecha_creacion=datetime.now(),
        estado="Confirmado",
        total=total,
        direccion_envio_id=direccion_id,
        proveedor_logistico=proveedor_logistico,
        numero_rastreo=f"TRK-{random.randint(100000,999999)}"
    )

    db.session.add(pedido)
    db.session.commit()  # para obtener el ID del pedido

    # 2. Crear detalles del pedido
    for item in carrito.values():
        detalle = DetallePedido(
            pedido_id=pedido.id,
            producto_id=item["id"],
            cantidad=item["cantidad"],
            precio_unitario=item["precio"]
        )
        db.session.add(detalle)

        # Reducir stock
        producto = Producto.query.get(item["id"])
        producto.stock_total -= item["cantidad"]

    # 3. Crear registro de transacción de pago
    transaccion = TransaccionPago(
        pedido_id=pedido.id,
        monto=total,
        estado="Aprobado",  # Simulación
        referencia_externa=f"PAY-{random.randint(10000,99999)}",
        fecha_transaccion=datetime.now()
    )
    db.session.add(transaccion)

    db.session.commit()

    # 4. Vaciar carrito
    session.pop("carrito", None)

    flash("¡Tu pedido fue registrado exitosamente!", "success")
    return redirect(url_for("rastrear_pedidos", pedido_id=pedido.id))

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        nombre=request.form.get("nombre")
        email=request.form.get("email")
        password=request.form.get("password")
        user_exist=Usuario.query.filter_by(email=email).first()
        if user_exist:
            flash("El Correo Ya Esta Registrado")
            return redirect(url_for("register"))
        password_hash = generate_password_hash(password)
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            contrasena_hash=password_hash,
            rol="Cliente"
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Cuenta creada exitosamente", "success")
        return redirect(url_for("login"))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "error")
        return redirect(url_for('login'))

    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for('login'))


@app.route('/cuenta/facturas')
def ver_facturas():
    if "user_id" not in session:
        return redirect("/login")

    facturas = db.session.query(
        Pedido.id,
        Pedido.fecha_creacion,
        Pedido.total,
        Pedido.estado,
        TransaccionPago.estado.label("estado_pago")
    ).join(
        TransaccionPago, Pedido.id == TransaccionPago.pedido_id
    ).filter(
        Pedido.cliente_id == session["user_id"]
    ).all()
    return render_template('dashboard.html',
                           section_title="Facturas y Pagos",
                           active_tab='facturas',
                           current_user=session['user_name'],
                           facturas=facturas)

@app.route('/cuenta/perfil',methods = ['GET','POST'])
def administrar_cuenta():
    if 'user_name' not in session:
        return redirect('login')
    usuario = Usuario.query.get(session['user_id'])
    direccion = usuario.direccion or Direccion(usuario_id=usuario.id)
    if request.method == 'POST':
        # Actualizar datos del usuario
        usuario.nombre = request.form['nombre']
        usuario.email = request.form['email']
        usuario.telefono = request.form['telefono']

        # Actualizar dirección
        direccion.nombre_direccion = request.form['nombre_direccion']
        direccion.linea1 = request.form['linea1']
        direccion.ciudad = request.form['ciudad']
        direccion.pais = request.form['pais']
        direccion.codigo_postal = request.form['codigo_postal']

        # Si es nueva dirección, agregarla
        if usuario.direccion is None:
            db.session.add(direccion)

        db.session.commit()

        flash("Datos actualizados correctamente.", "success")
        return redirect(url_for('dashboard'))
    direccion = usuario.direccion or Direccion(usuario_id=usuario.id)
    return render_template('dashboard.html',
                            section_title="Administrar Cuenta",
                            active_tab='perfil',
                            current_user=session['user_name'],
                            usuario=usuario,
                            direccion=direccion)

@app.route('/cuenta/pedidos')
def rastrear_pedidos():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para ver tus pedidos", "warning")
        return redirect(url_for('login'))

    usuario_id = session['user_id']

    pedido = (
        Pedido.query
        .filter_by(cliente_id=usuario_id)
        .order_by(Pedido.fecha_creacion.desc())
        .all()
    )
    return render_template('dashboard.html',
                           section_title="Rastrear Pedidos",
                           active_tab='pedidos',
                           current_user=session['user_name'], # Asumiendo que existe
                           pedidos=pedido) # Pasa la lista de pedidos

@app.route("/factura/<int:pedido_id>")
def factura_detalle(pedido_id):
    if "user_id" not in session:
        return redirect("/login")

    pedido = db.session.query(Pedido).filter_by(
        id=pedido_id, cliente_id=session["user_id"]
    ).first()

    if not pedido:
        return "Factura no encontrada", 404

    detalles = db.session.query(
        DetallePedido,
        Producto.nombre,
        Producto.descripcion
    ).join(Producto, DetallePedido.producto_id == Producto.id
    ).filter(DetallePedido.pedido_id == pedido_id).all()

    pago = TransaccionPago.query.filter_by(pedido_id=pedido_id).first()
    direccion = Direccion.query.filter_by(id=pedido.direccion_envio_id).first()

    return render_template(
        "factura_detalle.html",
        pedido=pedido,
        detalles=detalles,
        pago=pago,
        direccion=direccion
    )

#funcion para verificar si el rol pertenece a admin
def requiere_admin():
    if "user_id" not in session or session.get("user_role") != "Administrador":
        return redirect("/login")

@app.route("/admin/productos")
def admin_productos():
    requiere_admin()

    productos = Producto.query.all()
    return render_template("admin_productos.html", productos=productos)



# ============================
#   CREAR PRODUCTO
# ============================
@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
def admin_producto_nuevo():
    requiere_admin()

    categorias = Categoria.query.all()

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        categoria_id = request.form["categoria_id"]

        # ========== Manejo de imagen ==========
        imagen_file = request.files.get("imagen")
        nombre_imagen = None

        if imagen_file and imagen_file.filename != "":
            filename = secure_filename(imagen_file.filename)
            nombre_imagen = filename
            imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        nuevo = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock_total=stock,
            url_img=nombre_imagen
        )

        db.session.add(nuevo)
        db.session.commit()

        flash("Producto creado exitosamente", "success")
        return redirect("/admin/productos")

    return render_template("admin_producto_form.html", producto=None, categorias=categorias)


# ============================
#   EDITAR PRODUCTO
# ============================
@app.route("/admin/producto/editar/<int:id>", methods=["GET", "POST"])
def admin_producto_editar(id):
    requiere_admin()

    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.all()

    if request.method == "POST":
        producto.nombre = request.form["nombre"]
        producto.descripcion = request.form["descripcion"]
        producto.precio = request.form["precio"]
        producto.stock_total = request.form["stock"]
        # ========== Imagen (opcional) ==========
        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename != "":
            filename = secure_filename(imagen_file.filename)
            producto.url_img = filename
            imagen_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.session.commit()

        flash("Producto actualizado correctamente", "success")
        return redirect("/admin/productos")

    return render_template("admin_producto_form.html",
                           producto=producto,
                           categorias=categorias)


# ============================
#   ELIMINAR PRODUCTO
# ============================
@app.route("/admin/producto/eliminar/<int:id>")
def admin_producto_eliminar(id):
    requiere_admin()

    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()

    flash("Producto eliminado", "info")
    return redirect("/admin/productos")

@app.route("/admin/rebuild-recommender")
def rebuild_recommender():
    global recommender
    productos = Producto.query.all()
    recommender = ProductRecommender(productos)
    flash("Recomendador regenerado exitosamente", "success")
    return redirect("/admin/productos")


with app.app_context():
    productos = Producto.query.all()
    recommender = ProductRecommender(productos) if productos else None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
