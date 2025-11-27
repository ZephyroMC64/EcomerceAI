from . import db

producto_categoria = db.Table(
    'Producto_Categoria',
    db.Column('producto_id', db.Integer, db.ForeignKey('Productos.id'), primary_key=True),
    db.Column('categoria_id', db.Integer, db.ForeignKey('Categorias.id'), primary_key=True)
)
