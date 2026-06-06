INCLUSION - SISTEMA DE ORIENTACIÓN EDUCATIVA

DESCRIPCIÓN DEL PROYECTO

**INCLUSION** es una aplicación web desarrollada con **Flask** que facilita el proceso de orientación educativa y seguimiento de estudiantes. El sistema permite a orientadores, estudiantes y acudientes interactuar en un ambiente colaborativo para mejorar la inclusión educativa y el bienestar estudiantil.

FUNCIONALIDADES PRINCIPALES:
- **Gestión de usuarios** con tres roles: Orientador, Estudiante y Acudiente
- **Programación de sesiones de orientación**
- **Registro y seguimiento de inclusión**
- **Generación de reportes y evaluaciones**
- **Sistema de mensajería entre usuarios**
- **Interfaz responsiva y amigable**

---

REQUISITOS PREVIOS

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- **Python 3.8 o superior** - [Descargar](https://www.python.org/)
- **MySQL 5.7 o superior** - [Descargar](https://www.mysql.com/)
- **Git** (opcional, para clonar el proyecto) - [Descargar](https://git-scm.com/)

---

INSTALACIÓN Y CONFIGURACIÓN

1. CLONAR O DESCARGAR EL PROYECTO

Si usas Git:
git clone <URL-DEL-REPOSITORIO>
cd PROYECTO_grado/INCLUSION

O simplemente extrae la carpeta INCLUSION en tu equipo

2. CREAR UN ENTORNO VIRTUAL (RECOMENDADO)

En Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

En Windows (CMD):
python -m venv .venv
.venv\Scripts\activate.bat

En Linux/Mac:
python3 -m venv .venv
source .venv/bin/activate

3. INSTALAR LAS DEPENDENCIAS

pip install -r requirements.txt

**Dependencias instaladas:**
- `flask` - Framework web
- `flask-mysql` - Conector MySQL para Flask
- `werkzeug` - Utilidades de seguridad (hash de contraseñas)
- `mysql-connector-python` - Conector MySQL nativo

4. CONFIGURAR LA BASE DE DATOS

A. Crear la base de datos MySQL:

1. Abre MySQL Workbench o phpMyAdmin
2. Abre el archivo Base.sql ubicado en la carpeta del proyecto
3. IMPORTANTE: Ejecuta el script por partes, no completo:
   - Primero ejecuta la sección de creación de base de datos
   - Luego las tablas
   - Finalmente los inserts de datos

Paso 1: Crear la base de datos
DROP DATABASE orientacion;
CREATE DATABASE orientacion;
USE orientacion;

Paso 2: Crear las tablas (orientadores, estudiantes, acudientes, etc.)
Paso 3: Insertar datos de prueba

B. Crear el usuario de MySQL (importante):

Acceso con credenciales del proyecto:
CREATE USER 'flaskuser'@'localhost' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON orientacion.* TO 'flaskuser'@'localhost';
FLUSH PRIVILEGES;

**Nota**: El usuario actual es `flaskuser` sin contraseña (configurado en `app.py`).

5. VERIFICAR LA CONFIGURACIÓN EN app.py

Abre app.py y verifica los datos de conexión a la base de datos:

DB_CONFIG = {
    'host': 'localhost',      # Dirección del servidor MySQL
    'user': 'flaskuser',      # Usuario de la BD
    'password': '',           # Contraseña (vacía en configuración actual)
    'database': 'orientacion' # Nombre de la BD
}

Si tu configuración es diferente, actualiza estos valores según tu entorno.

---

EJECUTAR LA APLICACIÓN

1. ACTIVAR EL ENTORNO VIRTUAL (si no está activo)

Windows PowerShell:
.\.venv\Scripts\Activate.ps1

Windows CMD:
.venv\Scripts\activate.bat

Linux/Mac:
source .venv/bin/activate

2. EJECUTAR LA APLICACIÓN FLASK

python app.py

Deberías ver algo como:

 * Running on http://127.0.0.1:5000
 * Debug mode: on

3. ACCEDER A LA APLICACIÓN

Abre tu navegador web y ve a:

http://localhost:5000

---

ESTRUCTURA DEL PROYECTO

INCLUSION/
├── app.py                    # Archivo principal de la aplicación Flask
├── Base.sql                  # Script de creación de la base de datos
├── requirements.txt          # Dependencias del proyecto
├── README.md                 # Este archivo
├── Templates/                # Plantillas HTML
│   ├── Index.html           # Página de inicio
│   ├── login.html           # Formulario de login
│   ├── Registrate.html      # Registro de nuevos usuarios
│   ├── estudiante.html      # Panel de estudiante
│   ├── orientador.html      # Panel de orientador
│   ├── acudiente.html       # Panel de acudiente
│   ├── orientador_mensajes.html  # Sistema de mensajería
│   ├── reportes.html        # Generación de reportes
│   ├── contactanos.html     # Formulario de contacto
│   └── terminos.html        # Términos y condiciones
└── static/                   # Archivos estáticos
    ├── css/                  # Estilos CSS
    │   ├── login.css
    │   ├── estudiante.css
    │   ├── orientador.css
    │   ├── acudiente.css
    │   ├── reportes.css
    │   └── ...
    ├── img/                  # Imágenes
    ├── ico/                  # Iconos
    └── uploads/              # Archivos subidos por usuarios
        └── reportes/         # Reportes generados

---

ROLES Y USUARIOS

1. ORIENTADOR
- Acceso a panel de orientación
- Gestión de sesiones con estudiantes
- Creación de registros de inclusión
- Generación de reportes
- Contacto con acudientes

Usuario de prueba:
Correo: admin@colegio.com
Contraseña: admin1234

2. ESTUDIANTE
- Ver sesiones programadas
- Acceso a registros personales
- Visualizar reportes
- Comunicarse con orientador y acudiente

3. ACUDIENTE
- Seguimiento del estudiante
- Acceso a reportes
- Comunicación con orientador
- Información de sesiones

---

CONFIGURACIÓN AVANZADA

Cambiar Puerto
Por defecto, Flask corre en localhost:5000. Para cambiar el puerto, modifica:

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)  # Puerto 8000

Cambiar Clave Secreta
Por seguridad, cambia la clave secreta en app.py:

app.secret_key = os.environ.get('FLASK_SECRET', 'tu_nueva_clave_secreta_fuerte')

Habilitar HTTPS
Para producción, usa un servidor WSGI como Gunicorn:

pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

---

BASE DE DATOS - TABLAS PRINCIPALES

| Tabla | Descripción |
|-------|------------|
| `orientadores` | Datos de orientadores (id, nombre, correo, contraseña, especialización) |
| `estudiantes` | Información de estudiantes |
| `acudientes` | Datos de acudientes y su relación con estudiantes |
| `sesion_orientacion` | Sesiones programadas entre orientador y estudiante |
| `registro_inclusion` | Registros de inclusión y seguimiento |
| `informe_evaluacion` | Evaluaciones y recomendaciones |
| `mensajes_contacto` | Formulario de contacto y mensajería |

---

SOLUCIÓN DE PROBLEMAS COMUNES

Error: "ModuleNotFoundError: No module named 'flask'"
Solución: Asegúrate de estar en el entorno virtual activado e instala las dependencias:
pip install -r requirements.txt

Error: "Access denied for user 'flaskuser'@'localhost'"
Solución: Verifica que:
- MySQL esté corriendo
- El usuario flaskuser existe
- La base de datos orientacion está creada

Verificar en MySQL:
mysql -u root -p
SELECT user FROM mysql.user;
USE orientacion;
SHOW TABLES;

Error: "Unable to import module mysql.connector"
Solución:
pip install mysql-connector-python

Error: "Timezone offset must be between -14:00 and +14:00"
Solución: Verifica la zona horaria en Base.sql y en tu servidor MySQL

---

NOTAS IMPORTANTES

SEGURIDAD:
- Cambia las contraseñas por defecto antes de producción
- Guarda la SECRET_KEY en una variable de entorno
- Usa HTTPS en producción
- Actualiza regularmente los paquetes

BASE DE DATOS:
- Haz backups regularmente
- Las contraseñas de estudiantes y acudientes deben estar hasheadas
- Las contraseñas de orientadores actualmente están en texto plano (modificar para producción)

---

SOPORTE Y CONTRIBUCIONES

Para reportar bugs, sugerencias o contribuir al proyecto:

1. Revisa el código en [Código fuente]
2. Crea un issue describiendo el problema
3. Envía un pull request con las mejoras

LICENCIA

Este proyecto fue desarrollado como proyecto de grado.

CHECKLIST DE INICIO RÁPIDO

- [ ] Python 3.8+ instalado
- [ ] MySQL 5.7+ instalado y corriendo
- [ ] Entorno virtual creado (`python -m venv .venv`)
- [ ] Entorno virtual activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Base de datos creada (`Base.sql` ejecutado por partes)
- [ ] Usuario MySQL `flaskuser` creado
- [ ] `app.py` configurado con datos correctos
- [ ] Aplicación ejecutada (`python app.py`)
- [ ] Navegador abierto en `http://localhost:5000`
