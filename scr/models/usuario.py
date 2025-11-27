from . import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = 'Usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    rol = db.Column(db.Enum('Cliente', 'Administrador', 'Vendedor'), default='Cliente', nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    direccion = db.relationship("Direccion", backref="usuario", uselist=False)

    def __repr__(self):
            return f'<Usuario {self.email}>'

class Direccion(db.Model):
    __tablename__ = "Direcciones"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuarios.id"), nullable=False)
    nombre_direccion = db.Column(db.String(50))
    linea1 = db.Column(db.String(255), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(20))
