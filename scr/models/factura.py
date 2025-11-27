from . import db

class Pedido(db.Model):
    __tablename__ = 'Pedidos'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('Usuarios.id'))
    fecha_creacion = db.Column(db.DateTime)
    estado = db.Column(db.Enum('Pendiente', 'Confirmado', 'Enviado', 'Entregado', 'Devuelto', 'Cancelado'))
    total = db.Column(db.Numeric(10, 2))
    direccion_envio_id = db.Column(db.Integer, db.ForeignKey('Direcciones.id'))
    numero_rastreo = db.Column(db.String(100))
    proveedor_logistico = db.Column(db.String(50))

    detalles = db.relationship("DetallePedido", backref="pedido", lazy=True)
    transaccion = db.relationship("TransaccionPago", uselist=False, backref="pedido")


class DetallePedido(db.Model):
    __tablename__ = 'Detalle_Pedido'

    pedido_id = db.Column(db.Integer, db.ForeignKey('Pedidos.id'), primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('Productos.id'), primary_key=True)
    cantidad = db.Column(db.Integer)
    precio_unitario = db.Column(db.Numeric(10, 2))

    producto = db.relationship("Producto")


class TransaccionPago(db.Model):
    __tablename__ = 'Transacciones_Pago'

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('Pedidos.id'), unique=True)
    monto = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.Enum('Aprobado', 'Rechazado', 'Reembolsado'))
    referencia_externa = db.Column(db.String(255))
    fecha_transaccion = db.Column(db.DateTime)
