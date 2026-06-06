# Proyecto de grado: Plataforma de Orientación e Inclusión Educativa
# Autor: ING Daniel Jose Gomez Supelano 
# Fecha: 2024-05-7 - 2025/10/28
# ESTE ARCHIVO: app.py - Archivo principal de la aplicación Flask, contiene la configuración, rutas y lógica principal del backend para manejar la autenticación, gestión de usuarios, sesiones de orientación, reportes y mensajes de contacto. 

# Importar librerias 

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import mysql.connector                      # Librería para conectar con MySQL 
from werkzeug.security import generate_password_hash, check_password_hash              #librería para contraseñas
import os              # para manejo de archivos y rutas
from functools import wraps                 # para crear decoradores de funciones (ej: require_role)
import sys                   # para manejo de excepciones y errores
from datetime import datetime
from werkzeug.utils import secure_filename

#  CONFIGURACIÓN GENERAL DE LA APLICACIÓN FLASK

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'una_clave_secreta_fuerte_y_larga_456')

# PARÁMETROS DE CONEXIÓN A LA BASE DE DATOS MySQL

DB_CONFIG = {
    'host': 'localhost', # Cambia a '
    'user': 'flaskuser',     # Usuario de la base de datos
    'password': '',          # Sin contraseña
    'database': 'orientacion' # nombre de la base de datos
}

# Diccionario que asocia roles con tablas en la BD
TIPO_USUARIOS = {
    'orientador': 'orientadores', # rol orientador se conecta a tabla orientadores
    'estudiante': 'estudiantes', # rol estudiante se conecta a tabla estudiantes
    'acudiente': 'acudientes' # rol acudiente se conecta a tabla acudientes
}

# FUNCIÓN DE CONEXIÓN A LA BASE DE DATOS
def get_connection(): # función para obtener una conexión a la base de datos MySQL usando mysql.connector
    """Devuelve una conexión nueva a MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            auth_plugin='mysql_native_password',
            charset='utf8mb4'
        )
        return conn # Devuelve la conexión establecida
    except mysql.connector.Error as e: 
        # Evita error OSError: [Errno 22] en Windows al imprimir mensajes con tildes o caracteres especiales
        print("Error al conectar a la base de datos:", str(e).encode('utf-8', 'ignore').decode())
        raise
# DECORADOR DE SEGURIDAD PARA ROLES
def require_role(role_name):
    """Decorador para restringir el acceso a rutas según el rol."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Debes iniciar sesión para acceder.", "danger")
                return redirect(url_for('login'))

            if session.get('user_tipo') != role_name.lower():
                flash(f"No tienes permisos de {role_name}.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
# RUTAS PRINCIPALES
@app.route('/') # Ruta para la página principal
def home(): 
    """Página principal"""
    return render_template('index.html')  #  el template index.html para la página de inicio

@app.route('/login', methods=['GET', 'POST']) # Ruta para el inicio de sesión, acepta tanto GET (mostrar formulario) como POST (procesar datos)
def login(): # Función para manejar el inicio de sesión de los usuarios
    """Inicio de sesión para todos los usuarios (Estudiante, Acudiente, Orientador)"""
    if request.method == 'POST': # Si el método es POST, procesa el formulario de login
        email = request.form.get('email', '').strip() # Obtiene el correo electrónico del formulario, eliminando espacios en blanco
        password = request.form.get('password', '')# Obtiene la contraseña del formulario
        if not email or not password:
            flash("Completa todos los campos", "warning") # Si falta el correo o la contraseña, muestra un mensaje de advertencia y redirige al login
            return redirect(url_for('login')) # Redirige al login para que el usuario intente de nuevo

        user = None # Variable para almacenar los datos del usuario encontrado
        user_tipo_lower = None # Variable para almacenar el tipo de usuario (orientador, acudiente, estudiante)
        conn = None # Variable para la conexión a la base de datos, se inicializa en None para manejarla correctamente en el bloque finally

        try: # Intenta conectar a la base de datos y buscar al usuario en las tablas correspondientes según el tipo
            conn = get_connection() # Obtiene una conexión a la base de datos
            cur = conn.cursor(dictionary=True)

            # Buscar en cada tabla según el tipo
            for tipo, table in TIPO_USUARIOS.items(): # Itera sobre el diccionario de tipos de usuarios y sus tablas asociadas
                cur.execute(f"""
                    SELECT id, correo, password, nombre, apellido 
                    FROM {table} 
                    WHERE correo = %s AND status = TRUE
                """, (email,)) # Ejecuta una consulta SQL para buscar un usuario activo con el correo proporcionado 
                temp_user = cur.fetchone()
                
                # Si se encuentra un usuario, verifica la contraseña. Para orientadores, la contraseña se compara en texto plano (no recomendado para producción). Para estudiantes y acudientes, se utiliza check_password_hash para comparar la contraseña cifrada.
                if temp_user:
                    if tipo == "orientador": # si es orientador 
                        if password == temp_user['password']: # compara la contraseña en texto plano
                            user_tipo_lower = tipo
                            break 
                    else: # para estudiantes y acudientes, la contraseña está cifrada en la base de datos,
                        if check_password_hash(temp_user['password'], password): # verifica la contraseña utilizando check_password_hash
                            user = temp_user # si la contraseña es correcta, asigna el usuario encontrado a la variable user
                            user_tipo_lower = tipo
                            break
            cur.close() # función para cerrar el cursor después de usarlo, para liberar recursos

            if user: # Si se encontró un usuario válido, se crean las variables de sesión para mantener la información del usuario durante su sesión activa
                session['user_id'] = user['id'] # campo id del usuario, se almacena en la sesión para identificar al usuario en futuras solicitudes
                session['user_email'] = user['correo'] # campo correo del usuario, se almacena en la sesión para mostrarlo o usarlo en otras partes de la aplicación
                session['user_nombre'] = f"{user['nombre']} {user['apellido']}" # se crea una variable de sesión que concatena el nombre y apellido del usuario para mostrarlo en el dashboard
                session['user_tipo'] = user_tipo_lower # se almacena el tipo de usuario (orientador, acudiente, estudiante) en la sesión para controlar el acceso a las rutas y mostrar información personalizada
                flash(f"Has iniciado sesión como {user_tipo_lower.capitalize()} correctamente ✅", "success") # Muestra un mensaje de éxito indicando que el inicio de sesión fue exitoso y el tipo de usuario que ha iniciado sesión

                if user_tipo_lower == 'orientador': # Si el usuario es un orientador, redirige al dashboard del orientador
                    return redirect(url_for('dashboard_orientador')) # Redirige a la función dashboard_orientador que muestra el dashboard específico para orientadores
                elif user_tipo_lower == 'acudiente':
                    return redirect(url_for('dashboard_acudiente'))
                elif user_tipo_lower == 'estudiante':
                    return redirect(url_for('dashboard_estudiante')) # Redirige a la función dashboard_estudiante 
                else:
                    return redirect(url_for('home'))
            else:
                flash("Correo o contraseña incorrectos ❌", "danger") # Si no se encontró un usuario válido o la contraseña es incorrecta
                return redirect(url_for('login'))

        except Exception as e:
            print("Error en login:", e) # Imprime el error en la consola para depuración
            flash("Error en el servidor. Intenta más tarde", "danger") # Muestra un mensaje de error genérico
            return redirect(url_for('login')) # Redirige al login para que el usuario intente de nuevo
        finally:
            if conn:
                conn.close() #cierra conexión a la base

    # Si es GET, muestra el formulario
    return render_template('login.html') 



@app.route('/registro', methods=['GET', 'POST']) # Ruta para el registro de nuevos usuarios, acepta tanto GET (mostrar formulario) c
def registro():
    """Registro de nuevos usuarios (Acudientes y Estudiantes)"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip() # Obtiene el nombre del formulario, eliminando espacios en blanco
        apellido = request.form.get('apellido', '').strip() # Obtiene el apellido del formulario, eliminando espacios en blanco
        correo = request.form.get('correo', '').strip() # Obtiene el correo del formulario, eliminando espacios en blanco
        password = request.form.get('password', '') # Obtiene la contraseña del formulario
        tipo_usuario = request.form.get('tipo_usuario', 'acudiente').lower() # Obtiene el tipo de usuario del formulario y lo convierte a minúsculas

        if not (nombre and apellido and correo and password): # Si falta alguno de los campos obligatorios
            flash("Rellena todos los campos obligatorios", "warning") 
            return redirect(url_for('registro')) # Redirige al registro para que el usuario complete los campos faltantes
        hashed = generate_password_hash(password) # Cifra la contraseña utilizando generate_password_hash para almacenarla de forma segura en la base de datos. Esto es especialmente importante para estudiantes y acudientes, ya que sus contraseñas no se almacenan en texto plano como en el caso de los orientadores
        conn = None

        try:
            conn = get_connection() # Obtiene una conexión a la base de datos
            cur = conn.cursor()

            if tipo_usuario == 'acudiente': # Si el tipo de usuario es acudiente, inserta un nuevo registro en la tabla acudientes con el nombre, apellido, correo y contraseña cifrada
                cur.execute("""
                    INSERT INTO acudientes (nombre, apellido, correo, password)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, apellido, correo, hashed)) # Ejecuta la consulta SQL para insertar el nuevo acudiente en la base de datos

            elif tipo_usuario == 'estudiante': # Si el tipo de usuario es estudiante, inserta un nuevo registro en la tabla estudiantes
                cur.execute("""
                    INSERT INTO estudiantes (nombre, apellido, correo, password)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, apellido, correo, hashed)) # Ejecuta la consulta SQL para insertar el nuevo estudiante en la base de datos

            else:
                flash("Tipo de usuario inválido", "danger") # Si el tipo de usuario no es válido, muestra un mensaje de error y redirige al registro
                return redirect(url_for('registro'))

            conn.commit() # Confirma la transacción para guardar los cambios en la base de datos
            flash(f"Registro de {tipo_usuario} completado. Ahora inicia sesión.", "success")
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError as e:
            conn.rollback() # Si ocurre un error de integridad (como un correo duplicado)
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for('registro'))

        except mysql.connector.Error as e:
            conn.rollback() # Si ocurre cualquier otro error relacionado con la base de datos
            flash(f"Error en la base de datos: {str(e)}", "danger")
            return redirect(url_for('registro'))

        finally:
            if conn:
                cur.close()# Cierra el cursor para liberar recursos
                conn.close() # Cierra la conexión a la base de datos para liberar recursos

    return render_template('Registrate.html') # Si el método es GET, muestra el formulario de registro para que el usuario pueda ingresar



@app.route('/contactanos', methods=['GET', 'POST'])
def contactanos(): # Ruta para la página de contacto
    if request.method == 'POST': 
        nombre = request.form.get('name', '').strip() # Obtiene el nombre del formulario, eliminando espacios en blanco
        correo = request.form.get('email', '').strip() # Obtiene el correo del formulario, eliminando espacios en blanco
        telefono = request.form.get('phone', '').strip() # Obtiene el teléfono del formulario
        asunto = request.form.get('subject', '').strip() # Obtiene el asunto del formulario, eliminando espacios en blanco
        mensaje = request.form.get('message', '').strip()# Obtiene el mensaje del formulario, eliminando espacios en blanco
        if not nombre or not correo or not asunto or not mensaje: 
            flash("Por favor completa los campos obligatorios.", "warning") # Si falta alguno de los campos obligatorios, muestra un mensaje de advertencia
            return redirect(url_for('contactanos')) # Redirige a la página de contacto para que el usuario complete los campos faltantes
        try:
            conn = get_connection() # Obtiene una conexión a la base de datos
            cursor = conn.cursor() # Crea un cursor para ejecutar consultas SQL
            sql = """INSERT INTO mensajes_contacto (nombre, correo, telefono, asunto, mensaje)VALUES (%s, %s, %s, %s, %s)""" # Consulta SQL para insertar un nuevo en mensajes_contacto
            cursor.execute(sql, (nombre, correo, telefono, asunto, mensaje)) # Ejecuta la consulta SQL con los datos proporcionados por el usuario en el formulario de contacto
            conn.commit()# Confirma la transacción para guardar el nuevo mensaje en la base de datos
            cursor.close() # Cierra el cursor para liberar recursos
            conn.close() # Cierra la conexión a la base de datos para liberar recursos
            flash("✅ Tu mensaje fue enviado correctamente.", "success") # Muestra un mensaje de éxito indicando 
            return redirect(url_for('contactanos'))
        except Exception as e:
            print("Error al guardar mensaje:", e) # Imprime el error en la consola para depuración
            flash("❌ Ocurrió un error al enviar el mensaje.", "danger") # Muestra un mensaje de error por guardar el mensaje en la base de datos
            return redirect(url_for('contactanos')) # Redirige a la página de contacto para que el usuario intente enviar el mensaje nuevamente
    return render_template('contactanos.html') 


@app.route('/terminos') # Ruta para la página de términos y condiciones
def terminos():
    """Términos y condiciones"""
    return render_template('terminos.html') # Renderiza el template terminos.html 

@app.route('/logout') # Ruta para cerrar sesión
def logout():
    """Cerrar sesión"""
    session.clear() # Limpia todas las variables de sesión para cerrar la sesión del usuario
    flash("Sesión cerrada correctamente.", "info") # Muestra un mensaje de información indicando que la sesión se ha cerrado correctamente
    return redirect(url_for('home'))# Redirige a la página principal después de cerrar sesión
# DASHBOARD DEL ORIENTADOR
@app.route('/orientador/dashboard')# Ruta para el dashboard de orientador
@require_role('orientador') # Utiliza el decorador require_role para restringir el acceso a esta ruta solo a usuarios con el rol de orientador
def dashboard_orientador():
    """Dashboard principal del orientador con mensajes de contacto"""
    orientador_id = session.get('user_id') # Obtiene el ID del orientador desde la sesión para personalizar la información mostrada en el dashboard.
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # Datos estadísticos
        cur.execute("SELECT COUNT(*) as total FROM estudiantes")# Ejecuta una consulta SQL para contar el total de estudiantes regidtrados en la base de datos
        total_estudiantes = cur.fetchone()['total']
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM sesion_orientacion 
            WHERE orientador_id = %s
        """, (orientador_id,)) # Ejecuta una consulta SQL para contar el total de sesiones de orientación 
        total_sesiones = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM registro_inclusion")# Ejecuta una consulta SQL para contar el total de registros en la tabla registro_inclusion
        total_registros = cur.fetchone()['total']# Ejecuta una consulta SQL para contar el total de registros en la tabla registro_inclusion
        
        # Últimas sesiones
        cur.execute("""
            SELECT 
                s.fecha, s.descripcion, s.tipo_sesion,
                e.nombre AS nombre_estudiante, 
                e.apellido AS apellido_estudiante 
            FROM sesion_orientacion s
            JOIN estudiantes e ON s.estudiante_id = e.id
            WHERE s.orientador_id = %s
            ORDER BY s.fecha DESC
            LIMIT 5
        """, (orientador_id,))
        ultimas_sesiones = cur.fetchall()

        # NUEVO: Mensajes de contacto
        cur.execute("""
            SELECT id, nombre, correo, telefono, asunto, mensaje
            FROM mensajes_contacto
            ORDER BY id DESC
        """) # Ejecuta una consulta SQL para obtener los mensajes de contacto más recientes
        mensajes = cur.fetchall()

        cur.close() # Cierra el cursor para liberar recursos

        return render_template('orientador.html', # Renderiza el template orientador.html 
                               total_estudiantes=total_estudiantes,
                               total_sesiones=total_sesiones,
                               total_registros=total_registros,
                               ultimas_sesiones=ultimas_sesiones,
                               mensajes=mensajes)
    except mysql.connector.Error as e:
        flash(f"Error al cargar datos del dashboard: {str(e)}", "danger") # Si ocurre un error al cargar los datos del dashboard
        return redirect(url_for('home'))
    finally:
        if conn:
            if 'cur' in locals() and cur:
                cur.close() # Cierra el cursor si fue creado
            conn.close()# Cierra la conexión a la base de datos para liberar recursos
# GESTIÓN DE MENSAJES DE CONTACTO (CRUD)
@app.route('/orientador/eliminar_mensaje/<int:id>', methods=['POST'])
@require_role('orientador') # Utiliza el decorador require_role para restringir el acceso a esta ruta solo a usuarios con el rol de orientador
def eliminar_mensaje(id):
    """Permite al orientador eliminar mensajes de contacto"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM mensajes_contacto WHERE id = %s", (id,))
        conn.commit()
        flash("Mensaje eliminado correctamente ✅", "info")
    except Exception as e:
        flash(f"Error al eliminar mensaje: {e}", "danger")
    finally:
        if conn:
            cur.close()
            conn.close()
    return redirect(url_for('dashboard_orientador'))

# LISTAR mensajes (READ)
@app.route('/orientador/mensajes')
@require_role('orientador')
def mensajes_orientador(): # Ruta para listar los mensajes de contacto en el dashboard del orientador
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM mensajes_contacto ORDER BY id DESC")
    mensajes = cur.fetchall()
    cur.close() # Cierra el cursor para liberar recursos
    conn.close() # Cierra la conexión a la base de datos para liberar recursos
    return render_template('orientador_mensajes.html', mensajes=mensajes)

    # ACTUALIZAR estado (UPDATE)
@app.route('/orientador/mensajes/estado/<int:id>', methods=['POST'])
@require_role('orientador') 
def actualizar_estado_mensaje(id):
    nuevo_estado = request.form.get('estado')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE mensajes_contacto SET estado = %s WHERE id = %s", (nuevo_estado, id)) # Ejecuta una consulta SQL para actualizar el estado del mensaje
    conn.commit()
    cur.close()
    conn.close() # Cierra la conexión a la base de datos para liberar recursos
    flash("Estado actualizado ✅", "success") # Muestra la actualización del estado del mensaje en el dashboard del orientador
    return redirect(url_for('mensajes_orientador')) # Redirige a la página de mensajes del orientador para mostrar el mensaje actualizado

#  ELIMINAR mensaje (DELETE)
@app.route('/orientador/mensajes/eliminar/<int:id>', methods=['POST'])
@require_role('orientador')
def eliminar_mensaje_orientador(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mensajes_contacto WHERE id = %s", (id,))
    conn.commit() # Confirma la transacción para eliminar el mensaje de contacto de la base de datos
    cur.close() # Cierra el cursor para liberar recursos
    conn.close() # Cierra la conexión a la base de datos para liberar recursos
    flash("Mensaje eliminado ❌", "info")
    return redirect(url_for('mensajes_orientador'))
# REPORTES Y SUBIDA DE PDFS
@app.route('/orientador/reportes') # Ruta para la página de reportes del orientador
@require_role('orientador') 
def orientador_reportes():
    return render_template('reportes.html') # Renderiza el template reportes.html 

@app.route('/orientador/reportes/guardar', methods=['POST']) # Ruta para guardar un nuevo reporte de inclusión
@require_role('orientador') # Restringir el acceso a esta ruta solo a usuarios con el rol de orientador
def guardar_reporte(): 
    orientador_id = session.get('user_id') # Obtiene el ID del orientador desde la sesión para asociar el reporte con el orientador que lo creó
    titulo = request.form.get('titulo') # Obtiene el título del reporte desde el formulario
    tipo = request.form.get('tipo') # Obtiene el tipo de reporte desde el formulario
    estudiante_val = request.form.get('estudiante')  # puede venir id o nombre
    fecha = request.form.get('fecha')
    descripcion = request.form.get('descripcion')
    pdf = request.files.get('pdf') 

    # validaciones básicas
    if not pdf or pdf.filename == '':
        flash("⚠️ Debes subir un archivo PDF", "danger")
        return redirect(url_for('orientador_reportes'))

    # guardar archivo
    filename = secure_filename(pdf.filename)
    pdf_path = os.path.join('static', 'uploads', 'reportes', filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.save(pdf_path)

    # resolver estudiante_id: si viene número, usarlo; si viene nombre, buscarlo en la BD
    estudiante_id = None
    try:
        if estudiante_val:
            # intento parsear como entero
            estudiante_id = int(estudiante_val)
        else:
            estudiante_id = None
    except ValueError:
        # vino texto (ej: "Lidia Martinez") -> buscar en la tabla estudiantes
        try:
            conn_lookup = get_connection()
            cur_lookup = conn_lookup.cursor(dictionary=True)
            # Intentos de búsqueda:
            # 1) coincidencia exacta en "nombre apellido"
            cur_lookup.execute("""
                SELECT id FROM estudiantes
                WHERE CONCAT(nombre, ' ', apellido) = %s
                LIMIT 1
            """, (estudiante_val,))
            r = cur_lookup.fetchone()
            if r:
                estudiante_id = r['id']
            else:
                # 2) búsqueda por nombre o apellido parcial (opcional)
                cur_lookup.execute("""
                    SELECT id FROM estudiantes
                    WHERE nombre LIKE %s OR apellido LIKE %s
                    LIMIT 1
                """, (f"%{estudiante_val}%", f"%{estudiante_val}%"))
                r2 = cur_lookup.fetchone()
                if r2:
                    estudiante_id = r2['id']
            cur_lookup.close()
            conn_lookup.close()
        except Exception as ex_lookup:
            print("Error buscando estudiante por nombre:", ex_lookup)
            estudiante_id = None

    # ahora insertamos en registro_inclusion usando columnas reales: fecha, descripcion, titulo, estudiante_id, pdf_path
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO registro_inclusion (fecha, descripcion, titulo, estudiante_id, pdf_path)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha, descripcion, titulo, estudiante_id, pdf_path))
        conn.commit()
        cur.close()
        flash("✅ Reporte guardado correctamente", "success")
    except Exception as e:
        print("Error al insertar registro_inclusion:", e)
        flash("❌ Error al guardar el reporte. Revisa la consola.", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('orientador_reportes'))

# DASHBOARD DE ACUDIENTE Y ESTUDIANTE

@app.route('/acudiente/dashboard') # Ruta para el dashboard del acudiente
@require_role('Acudiente') 
def dashboard_acudiente(): 
    """Dashboard para el Acudiente. Mostrará información del estudiante a cargo."""
    nombre = session.get('user_nombre', 'Usuario')  # Recupera el nombre del acudiente desde la sesión
    return render_template('acudiente.html', nombre=nombre) # Renderiza el template acudiente.html

@app.route('/estudiante/dashboard') # Ruta para el dashboard del estudiante
@require_role('Estudiante') 
def dashboard_estudiante(): 
    """Dashboard para el Estudiante. Mostrará sus sesiones y registros."""
    nombre = session.get('user_nombre', 'Usuario')  # Recupera el nombre del acudiente desde la sesión
    return render_template('estudiante.html', nombre=nombre) # Renderiza el template estudiante.html

# GENERACIÓN DE REPORTES EN PDF
@app.route('/orientador/reportes/estudiantes') # Ruta para descargar el reporte de estudiantes en PDF
@require_role('orientador')
def reporte_estudiantes_pdf():
    """Descargar reporte de estudiantes en PDF"""
    orientador_id = session.get('user_id')
    
    try:
        pdf_data = generar_pdf_estudiantes(orientador_id) 
        
        if pdf_data:
            response = make_response(pdf_data) # Crea una respuesta HTTP con el contenido del PDF generado
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=reporte_estudiantes_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            flash("Error al generar el reporte", "danger") # Si no se pudo generar el PDF
            return redirect('/orientador/reportes') 
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger")
        return redirect('/orientador/reportes') # Si ocurre un error al generar el PDF, muestra un mensaje de error y manda a pagina de reportes del orientador


@app.route('/orientador/reportes/sesiones') # Ruta para descargar el reporte de sesiones en PDF, con filtros de fecha
@require_role('orientador') # Restringir el acceso a esta ruta solo a usuarios con el rol de orientador
def reporte_sesiones_pdf():
    """Descargar reporte de sesiones en PDF"""
    orientador_id = session.get('user_id')
    fecha_inicio = request.args.get('fecha_inicio') 
    fecha_fin = request.args.get('fecha_fin')
    
    try:
        pdf_data = generar_pdf_sesiones(orientador_id, fecha_inicio, fecha_fin)# Llama a la función generar_pdf_sesiones con el ID del orientador y las fechas de inicio y fin para obtener el contenido del PDF generado. Esta función debe encargarse de consultar la base de datos, filtrar las sesiones según las fechas proporcionadas.
        
        if pdf_data:
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=reporte_sesiones_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            flash("Error al generar el reporte", "danger")
            return redirect('/orientador/reportes') # Si no se pudo generar el PDF.
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger") # Si ocurre un error al generar el PDF.
        return redirect('/orientador/reportes') # Si ocurre un error al generar el PDF.


@app.route('/orientador/reportes/completo') # Ruta para descargar el reporte completo en PDF.
@require_role('orientador') # Restringir el acceso a esta ruta solo a usuarios con el rol de orientador
def reporte_completo_pdf():
    """Descargar reporte completo"""
    orientador_id = session.get('user_id') 
    
    try:
        pdf = PDF_Reporte(titulo='Reporte Completo de Orientación')
        pdf.alias_nb_pages() # Permite mostrar el número total de páginas en el pie de página del PDF
        pdf.add_page() # Agrega una nueva página al PDF para comenzar a escribir el contenido del reporte completo.
        
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        
        # SECCIÓN ESTUDIANTES
        pdf.set_font('Arial', 'B', 14) 
        pdf.cell(0, 10, 'ESTUDIANTES ASIGNADOS', 0, 1, 'L')
        pdf.ln(5)
        
        cur.execute("""
            SELECT 
                e.id, 
                CONCAT(e.nombre, ' ', e.apellido) as nombre_completo,
                e.edad, 
                e.grado, 
                COALESCE(e.promedio, 0) as promedio
            FROM estudiantes e
            WHERE e.orientador_id = %s AND e.status = TRUE
            ORDER BY e.nombre ASC
        """, (orientador_id,))
        estudiantes = cur.fetchall() # Ejecuta una consulta SQL para obtener la lista de estudiantes asignados al orientador, incluyendo su ID, nombre completo, edad, grado y promedio.
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(10, 8, 'ID', 1, 0, 'C')
        pdf.cell(70, 8, 'Nombre', 1, 0, 'C')
        pdf.cell(20, 8, 'Edad', 1, 0, 'C')
        pdf.cell(50, 8, 'Grado', 1, 0, 'C')
        pdf.cell(30, 8, 'Promedio', 1, 0, 'C')
        pdf.ln() # Salto de línea después de la fila de encabezados
        
        pdf.set_font('Arial', '', 9) # Establece la fuente para el contenido de los estudiantes.
        for est in estudiantes: # itera lista de estudiantes obtenida de la base de datos y agrega una fila en el PDF para cada estudiante, mostrando su ID, nombre completo, edad, grado y promedio.
            pdf.cell(10, 7, str(est['id']), 1, 0, 'C') #celda para el ID del estudiante, centrada
            pdf.cell(70, 7, est['nombre_completo'][:35], 1, 0, 'L')
            pdf.cell(20, 7, str(est['edad'] or 'N/A'), 1, 0, 'C')
            pdf.cell(50, 7, est['grado'][:25] or 'N/A', 1, 0, 'L')
            pdf.cell(30, 7, str(est['promedio']), 1, 0, 'C')
            pdf.ln() # Salto de línea después de cada fila de estudiante para separar visualmente los registros en el PDF.
        
        pdf.ln(10) # Salto de línea adicional para separar la sección de estudiantes de la siguiente sección de sesiones en el PDF.
        
        # SECCIÓN SESIONES
        pdf.set_font('Arial', 'B', 14) # Establece la fuente para el título de la sección de sesiones en el PDF.
        pdf.cell(0, 10, 'SESIONES RECIENTES', 0, 1, 'L')
        pdf.ln(5)
        # Ejecuta una consulta SQL para obtener las sesiones de orientación más recientes del orientador, incluyendo la fecha, hora de inicio, nombre del estudiante asociado, tipo de sesión y descripción.
        cur.execute("""
            SELECT 
                s.fecha,
                s.hora_inicio,
                CONCAT(e.nombre, ' ', e.apellido) as estudiante,
                s.tipo_sesion,
                s.descripcion
            FROM sesion_orientacion s
            JOIN estudiantes e ON s.estudiante_id = e.id
            WHERE s.orientador_id = %s
            ORDER BY s.fecha DESC
            LIMIT 10
        """, (orientador_id,))
        sesiones = cur.fetchall() # consulta SQL para obtener las sesiones de orientación más recientes del orientador, incluyendo la fecha, hora de inicio, nombre del estudiante asociado, tipo de sesión y descripción.
        
        pdf.set_font('Arial', 'B', 9) # Establece la fuente para los encabezados de la tabla de sesiones en el PDF.
        pdf.cell(25, 8, 'Fecha', 1, 0, 'C') # celda para la fecha de la sesión, centrada
        pdf.cell(25, 8, 'Hora', 1, 0, 'C') # celda para la hora de inicio de la sesión, centrada
        pdf.cell(60, 8, 'Estudiante', 1, 0, 'C') # celda para el nombre del estudiante asociado, centrada
        pdf.cell(30, 8, 'Tipo', 1, 0, 'C') # celda para el tipo de sesión, centrada
        pdf.cell(40, 8, 'Descripción', 1, 0, 'C') # celda para la descripción de la sesión, centrada
        pdf.ln()
        
        pdf.set_font('Arial', '', 8) #fuente para el contenido de las sesiones en el PDF.
        for ses in sesiones: # itera lista de sesiones obtenida de la base de datos y agrega una fila en el PDF para cada sesión, mostrando la fecha, hora de inicio, nombre del estudiante asociado, tipo de sesión y descripción.
            pdf.cell(25, 7, ses['fecha'].strftime('%d/%m/%Y'), 1, 0, 'C')
            pdf.cell(25, 7, ses['hora_inicio'].strftime('%H:%M'), 1, 0, 'C')
            pdf.cell(60, 7, ses['estudiante'][:30], 1, 0, 'L')
            pdf.cell(30, 7, ses['tipo_sesion'], 1, 0, 'C')
            pdf.cell(40, 7, (ses['descripcion'] or 'N/A')[:20], 1, 0, 'L')
            pdf.ln()
        
        cur.close() # Cierra el cursor para liberar recursos después de obtener los datos necesarios para el reporte completo.
        conn.close() # Cierra la conexión a la base de datos para liberar recursos después de obtener los datos necesarios para el reporte completo.
        
        pdf_data = pdf.output(dest='S').encode('latin-1')
        
        response = make_response(pdf_data) # Crea una respuesta HTTP con el contenido del PDF generado, codificado en latin-1 para asegurar la compatibilidad con caracteres especiales.
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=reporte_completo_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response # Devuelve la respuesta HTTP con el contenido del PDF generado, estableciendo los encabezados para indicar que es un archivo PDF y sugerir un nombre de archivo para la descarga. 
        # Si el PDF se genera correctamente, se crea una respuesta HTTP con el contenido del PDF y se establecen los encabezados para indicar que es un archivo PDF.
    except Exception as e:
        flash(f"Error: {str(e)}", "danger") # Si ocurre un error durante la generación del PDF, muestra menasaje
        return redirect('/orientador/reportes')# Si ocurre un error durante la generación del PDF, se muestra un mensaje de error y se redirige a la página de reportes del orientador.
#  EJECUCIÓN DEL SERVIDOR LOCAL.
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
