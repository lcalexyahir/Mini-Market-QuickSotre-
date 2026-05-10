-- Crear base de datos (ejecutar manualmente si no existe)
-- CREATE DATABASE MiniMarketOF;

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Permisos
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    module VARCHAR(50) NOT NULL
);

-- Tabla de Usuario-Permisos (relación muchos a muchos)
CREATE TABLE IF NOT EXISTS user_permissions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, permission_id)
);

-- Tabla de Clientes
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(15),
    address TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Asistencias
CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    check_in TIMESTAMP NOT NULL,
    check_out TIMESTAMP,
    date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar permisos base
INSERT INTO permissions (name, description, module) VALUES
('user_create', 'Crear nuevos usuarios', 'Administración de Usuarios'),
('user_read', 'Ver lista de usuarios', 'Administración de Usuarios'),
('user_update', 'Editar usuarios', 'Administración de Usuarios'),
('user_delete', 'Eliminar usuarios', 'Administración de Usuarios'),
('permission_assign', 'Asignar permisos a usuarios', 'Administración de Usuarios'),
('permission_read', 'Ver permisos', 'Administración de Usuarios'),
('client_create', 'Crear clientes', 'Administración de Usuarios'),
('client_read', 'Ver clientes', 'Administración de Usuarios'),
('client_update', 'Editar clientes', 'Administración de Usuarios'),
('client_delete', 'Eliminar clientes', 'Administración de Usuarios'),
('attendance_register', 'Registrar asistencia', 'Registro de Entrada y Salida'),
('attendance_read', 'Ver historial de asistencias', 'Registro de Entrada y Salida')
ON CONFLICT (name) DO NOTHING;

-- Insertar usuario administrador por defecto (password: admin123)
-- La contraseña en hash bcrypt es para 'admin123'
INSERT INTO users (username, email, password_hash, full_name, is_active) VALUES
('admin', 'admin@minimarket.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYEcE4XjZPu', 'Administrador del Sistema', true)
ON CONFLICT (username) DO NOTHING;

-- Dar todos los permisos al admin
INSERT INTO user_permissions (user_id, permission_id, granted_by)
SELECT 1, id, 1 FROM permissions
ON CONFLICT DO NOTHING;

-- Índices para mejorar rendimiento
CREATE INDEX idx_attendances_user_date ON attendances(user_id, date);
CREATE INDEX idx_attendances_check_in ON attendances(check_in);
CREATE INDEX idx_clients_document_id ON clients(document_id);
CREATE INDEX idx_users_username ON users(username);