from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .producto import Producto
from .categoria import Categoria
from .usuario import Usuario, Direccion
from .factura import Pedido, DetallePedido 