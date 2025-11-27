from . import db

class Categoria(db.Model):
    __tablename__ = 'Categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Categoria {self.nombre}>'
