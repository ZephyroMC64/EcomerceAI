from . import db
from .asociaciones import producto_categoria 

class Producto(db.Model):
    __tablename__ = 'Productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    url_img = db.Column(db.String(50), unique=True)
    stock_total = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)

    categorias = db.relationship(
        'Categoria',
        secondary=producto_categoria,
        backref='productos'
    )

    def __repr__(self):
        return f'<Producto {self.nombre}>'
