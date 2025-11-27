drop database ecommerce_inteligente_simple;
CREATE DATABASE IF NOT EXISTS ecommerce_inteligente_simple;
USE ecommerce_inteligente_simple;

-- ######################################
-- 2. TABLAS DE USUARIOS Y DIRECCIONES (Consolidación)
-- ######################################

-- Tabla principal de Usuarios (Consolida Usuarios y Clientes)
-- Asumimos que inicialmente solo trabajamos con Clientes y Administradores.
CREATE TABLE Usuarios (
    id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(100) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL, -- Nombre movido aquí
    telefono VARCHAR(20),        -- Teléfono movido aquí
    rol ENUM('Cliente', 'Administrador', 'Vendedor') NOT NULL DEFAULT 'Cliente',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Tabla simplificada de Direcciones (Asociada directamente a Usuarios)
CREATE TABLE Direcciones (
    id INT NOT NULL AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    nombre_direccion VARCHAR(50) COMMENT 'Ej: "Casa" o "Trabajo"',
    linea1 VARCHAR(255) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    codigo_postal VARCHAR(20),
    PRIMARY KEY (id),
    FOREIGN KEY (usuario_id) REFERENCES Usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ######################################
-- 3. TABLAS DE CATÁLOGO E INVENTARIO 
-- ######################################

-- Tabla de Productos 
CREATE TABLE Productos (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    url_img VARCHAR(50) UNIQUE,
    stock_total INT NOT NULL DEFAULT 0, 
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (id)
) ENGINE=InnoDB;


CREATE TABLE Categorias (
    id INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB;


CREATE TABLE Producto_Categoria (
    producto_id INT NOT NULL,
    categoria_id INT NOT NULL,
    PRIMARY KEY (producto_id, categoria_id),
    FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES Categorias(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ######################################
-- 4. TABLAS DE PEDIDOS Y LOGÍSTICA
-- ######################################

CREATE TABLE Pedidos (
    id INT NOT NULL AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Pendiente', 'Confirmado', 'Enviado', 'Entregado', 'Devuelto', 'Cancelado') NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    direccion_envio_id INT NOT NULL,
    numero_rastreo VARCHAR(100), -- **Consolidación**: El número de rastreo se mueve aquí
    proveedor_logistico VARCHAR(50), -- **Consolidación**: El proveedor se mueve aquí
    PRIMARY KEY (id),
    FOREIGN KEY (cliente_id) REFERENCES Usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (direccion_envio_id) REFERENCES Direcciones(id) ON DELETE RESTRICT
) ENGINE=InnoDB;


CREATE TABLE Detalle_Pedido (
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (pedido_id, producto_id),
    FOREIGN KEY (pedido_id) REFERENCES Pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE RESTRICT
) ENGINE=InnoDB;


CREATE TABLE Transacciones_Pago (
    id INT NOT NULL AUTO_INCREMENT,
    pedido_id INT NOT NULL UNIQUE,
    monto DECIMAL(10, 2) NOT NULL,
    estado ENUM('Aprobado', 'Rechazado', 'Reembolsado') NOT NULL,
    referencia_externa VARCHAR(255),
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (pedido_id) REFERENCES Pedidos(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. TABLAS DE RECOMENDACIONES 

CREATE TABLE Recomendaciones (
    cliente_id INT NOT NULL,
    producto_id INT NOT NULL,
    score DECIMAL(5, 4) COMMENT 'Puntaje de relevancia de la IA',
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cliente_id, producto_id), 
    FOREIGN KEY (cliente_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES Productos(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

COMMIT;


INSERT INTO Categorias (nombre) VALUES
('Electrónica'),
('Moda y Vestuario'),
('Hogar y Cocina'),
('Libros y Medios'),
('Deportes y Fitness');

INSERT INTO Productos (nombre, descripcion, precio, url_img, stock_total, activo) VALUES
('Smartphone Alpha X', 'Potente smartphone con cámara de 108MP y batería de larga duración.', 300.000, 'alpha_x.jpg', 50, TRUE),
('Smartwatch Fit Pro', 'Reloj inteligente con monitorización de salud avanzada y GPS.', 550.000, 'fit_pro.jpg', 120, TRUE),
('Audífonos Inalámbricos HD', 'Auriculares con cancelación de ruido activa y sonido de alta fidelidad.', 89.99, 'audifonos_hd.jpg', 80, TRUE),
('Sudadera Oversize Algodón', 'Sudadera cómoda y con estilo de algodón orgánico.', 80.000, 'sudadera_os.jpg', 200, TRUE),
('Juego de Sartenes Antiadherentes', 'Set de 3 sartenes de alta calidad para cocina profesional.', 180.000, 'sartenes_3.jpg', 60, TRUE),
('Novela Clásica: El Viajero', 'Edición especial de tapa dura de una novela atemporal.', 55.000, 'novela_viajero.jpg', 300, TRUE);

INSERT INTO Producto_Categoria (producto_id, categoria_id) VALUES
(1, 1),  -- Smartphone -> Electrónica
(2, 1),  -- Smartwatch -> Electrónica
(3, 1),  -- Audífonos -> Electrónica
(4, 2),  -- Sudadera -> Moda y Vestuario

-- Puedes asignar un producto a varias categorías si es relevante:
(5, 3),  -- Sartenes -> Hogar y Cocina
(5, 4),  -- Sartenes -> (Si tuvieras una categoría "Utensilios") - [Ejemplo de N:M]

(6, 4);  -- Novela -> Libros y Medios


INSERT INTO Pedidos (
    cliente_id, estado, total, direccion_envio_id,
    numero_rastreo, proveedor_logistico
) VALUES (
    1, 'Enviado', 250000, 1,
    'TRK123456789CO', 'Servientrega'
);
INSERT INTO Detalle_Pedido (pedido_id, producto_id, cantidad, precio_unitario)
VALUES (1, 1, 2, 125000);

INSERT INTO Transacciones_Pago (pedido_id, monto, estado, referencia_externa)
VALUES (1, 250000, 'Aprobado', 'PAY123ABC987');

select * from usuarios