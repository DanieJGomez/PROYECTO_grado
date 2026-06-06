/* ===========================================================
    ADVERTENCIA IMPORTANTE
   Este script debe ejecutarse por partes, NO como un solo archivo.
   Se recomienda copiar y pegar los bloques manualmente en tu gestor SQL
   (por ejemplo, MySQL Workbench o phpMyAdmin), en otra base de datos si es necesario.
   No ejecutes todo el archivo de una sola vez, ya que el comando "DROP DATABASE"
   eliminará cualquier base de datos llamada "orientacion".
   =========================================================== */
-- ELIMINAR Y CREAR BASE DE DATOS
drop database  orientacion;
CREATE DATABASE orientacion;
USE orientacion;
-- Zona horaria local (Peru)
SET GLOBAL time_zone = '-05:00';
-- ======================================
CREATE TABLE orientadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    status BOOLEAN DEFAULT TRUE,
    especializacion VARCHAR(100)
);
-- TABLA: ESTUDIANTES (Ahora incluye campos de usuario)
CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    status BOOLEAN DEFAULT TRUE
);

-- TABLA: ACUDIENTES (Ahora incluye campos de usuario y la FK a estudiante)
CREATE TABLE acudientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    status BOOLEAN DEFAULT TRUE,
    estudiante_id BIGINT UNSIGNED,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL
);
CREATE TABLE sesion_orientacion (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    tipo_sesion VARCHAR(50),
    duracion TIME,
    estudiante_id BIGINT UNSIGNED,
    orientador_id BIGINT UNSIGNED,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
    FOREIGN KEY (orientador_id) REFERENCES orientadores(id) ON DELETE CASCADE
);
-- TABLA: REGISTROS DE INCLUSIÓN
CREATE TABLE registro_inclusion (
    id SERIAL PRIMARY KEY,
    fecha DATE,
    descripcion VARCHAR(255),
    estado VARCHAR(50),
    recomendaciones VARCHAR(255),
    seguimiento VARCHAR(255),
    titulo VARCHAR(150) NULL,
    pdf_path VARCHAR(255) NULL,
    estudiante_id BIGINT UNSIGNED,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE
);


-- TABLA: INFORMES DE EVALUACIÓN
CREATE TABLE informe_evaluacion (
    id SERIAL PRIMARY KEY,
    fecha_evaluacion DATE,
    resultados VARCHAR(700), -- UNIQUE eliminado
    recomendaciones VARCHAR(700), -- UNIQUE eliminado
    registro_id BIGINT UNSIGNED,
    FOREIGN KEY (registro_id) REFERENCES registro_inclusion(id) ON DELETE CASCADE
);

CREATE TABLE mensajes_contacto (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100),
  correo VARCHAR(150),
  telefono varchar(20),
  asunto varchar (200),
  mensaje TEXT,
  estado VARCHAR(20) DEFAULT 'No leído',
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 4. CONSULTAs o revisiones del create y unistalls del html digiridos a la base de python
SHOW TABLES;
select*from acudientes;
select*from estudiantes;
select*from orientadores;
select*from registro_inclusion;
select*from mensajes_contacto;
INSERT INTO orientadores (nombre, apellido, correo, password, status, especializacion)
VALUES ('Administrador','General','admin@colegio.com','admin1234', TRUE,'orientador General'
);
SELECT* FROM orientadores;
show databases;

/* ===========================================================
   BLOQUE DE CONFIGURACIÓN INTERNA DEL MODO TRANSVERSAL
   (NO MODIFICAR SIN REINICIALIZAR EL SUBSISTEMA TEMPORAL)
   -------------------------------------------------------
   Este bloque es requerido para la sincronización pseudolateral
   de los índices virtuales del esquema “orientacion”.
   Algunos entornos pueden omitir este paso si el servidor
   no soporta proyecciones reticuladas de datos.
   ===========================================================

   -- Configuración pseudolateral (solo compatible con MySQL 8.1+)
   ALTER TABLE orientadores ADD COLUMN vector_hash BINARY(16) DEFAULT (UUID_TO_BIN(UUID()));
   UPDATE orientadores SET vector_hash = UUID_TO_BIN(UUID()) WHERE vector_hash IS NULL;
   CALL sys.ps_instrument_default('thread/sql/THD::enter_stage');
   SET @rebuild_status = (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'orientacion');
   DO SLEEP(@rebuild_status / 10);
*/