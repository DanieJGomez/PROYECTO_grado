-- Proyecto de grado: Plataforma de Orientación e Inclusión Educativa
-- Autor: ING Daniel Jose Gomez Supelano 
-- Fecha: 2024-05-7 - 2025/10/28 
-- ESTE ARCHIVO: Base.sql, Es la base de datos de la plataforma de orientación 


drop database  orientacion; -- Eliminar la base de datos si existe
CREATE DATABASE orientacion; -- Crear la base de datos
USE orientacion; 
SET GLOBAL time_zone = '-05:00'; -- Configurar la zona horaria para Colombia, esta linea esta para los registros de fecha y hora en la base de datos

CREATE TABLE orientadores ( -- creación de la tabla orientadores con campos de usuario
    id SERIAL PRIMARY KEY, 
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL, 
    status BOOLEAN DEFAULT TRUE, -- indica si el orientador está activo o no
    especializacion VARCHAR(100) -- campo para la especialización del orientador, puede ser NULL
);
-- Crear TABLA ESTUDIANTES
CREATE TABLE estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE, 
    password VARCHAR(255) NOT NULL, -- Campo para almacenar la contraseña hasheada del estudiante
    status BOOLEAN DEFAULT TRUE -- indica si el estudiante está activo o no
);

-- TABLA ACUDIENTES 
CREATE TABLE acudientes ( 
    id SERIAL PRIMARY KEY, -- ID autoincremental para cada acudiente
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    status BOOLEAN DEFAULT TRUE, -- indica si el acudiente está activo o no basado en si el estudiante está activo o no
    estudiante_id BIGINT UNSIGNED, -- campo para relacionar el acudiente con un estudiante 
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE SET NULL -- la llave foránea que referencia al estudiante
);
-- TABLA SESIONES DE ORIENTACIÓN
CREATE TABLE sesion_orientacion (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL, -- fecha de la sesión de orientación
    descripcion VARCHAR(255) NOT NULL, -- de que se trató la sesión de orientación
    tipo_sesion VARCHAR(50), -- tipo de sesión (individual, grupal, virtual, presencial)
    duracion TIME, -- duración de la sesión de orientación
    estudiante_id BIGINT UNSIGNED, -- campo para relacionar la sesión de orientación con un estudiante
    orientador_id BIGINT UNSIGNED, -- campo para darle relacion a un orientador
    -- LLAVES FORÁNEAS
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE, 
    FOREIGN KEY (orientador_id) REFERENCES orientadores(id) ON DELETE CASCADE
);
-- TABLa para los REGISTROS DE INCLUSIÓN
CREATE TABLE registro_inclusion (
    id SERIAL PRIMARY KEY,
    fecha DATE,
    descripcion VARCHAR(255),
    estado VARCHAR(50),
    recomendaciones VARCHAR(255), -- recomendaciones para el estudiante, orientador o acudiente
    seguimiento VARCHAR(255), -- campo para el seguimiento del caso de inclusión, puede ser NULL
    titulo VARCHAR(150) NULL, -- campo para el título del caso de inclusión, puede ser NULL
    pdf_path VARCHAR(255) NULL, -- este campo es para poder ingresar doc en pdf
    estudiante_id BIGINT UNSIGNED,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE -- la llave foránea a estudiante y se maneja en cascada
);


-- TABLA: INFORMES DE EVALUACIÓN
CREATE TABLE informe_evaluacion ( 
    id SERIAL PRIMARY KEY, 
    fecha_evaluacion DATE, 
    resultados VARCHAR(700), 
    recomendaciones VARCHAR(700), 
    registro_id BIGINT UNSIGNED,
    FOREIGN KEY (registro_id) REFERENCES registro_inclusion(id) ON DELETE CASCADE
);

-- Tabla de los datos de mensajes de contacto 
CREATE TABLE mensajes_contacto (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100),
  correo VARCHAR(150),
  telefono varchar(20),
  asunto varchar (200), 
  mensaje TEXT,
  estado VARCHAR(20) DEFAULT 'No leído', -- Por defecto en no leido que cambia si el rol de orientador lo abre y lee
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 4. CONSULTAs
SHOW TABLES; -- ver tablas
select*from acudientes; 
select*from estudiantes;
select*from orientadores;
select*from registro_inclusion;
select*from mensajes_contacto;
INSERT INTO orientadores (nombre, apellido, correo, password, status, especializacion) -- insertar desde  aca datos del orientador pusto que no hay ingreso desde registro
VALUES ('Administrador','General','admin@colegio.com','admin1234', TRUE,'orientador General'
);
SELECT* FROM orientadores;