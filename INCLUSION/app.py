from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import sys
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
                    return redirect(url_for('dashboard_estudiante'))
                else:
                    return redirect(url_for('home'))
            else:
                flash("Correo o contraseña incorrectos ❌", "danger")
                return redirect(url_for('login'))

        except Exception as e:
            print("Error en login:", e)
            flash("Error en el servidor. Intenta más tarde", "danger")
            return redirect(url_for('login'))
        finally:
            if conn:
                conn.close()

    # Si es GET, muestra el formulario
    return render_template('login.html')



@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos usuarios (Acudientes y Estudiantes)"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        correo = request.form.get('correo', '').strip()
        password = request.form.get('password', '')
        tipo_usuario = request.form.get('tipo_usuario', 'acudiente').lower()

        if not (nombre and apellido and correo and password):
            flash("Rellena todos los campos obligatorios", "warning")
            return redirect(url_for('registro'))

        hashed = generate_password_hash(password)
        conn = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            if tipo_usuario == 'acudiente':
                cur.execute("""
                    INSERT INTO acudientes (nombre, apellido, correo, password)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, apellido, correo, hashed))

            elif tipo_usuario == 'estudiante':
                cur.execute("""
                    INSERT INTO estudiantes (nombre, apellido, correo, password)
                    VALUES (%s, %s, %s, %s)
                """, (nombre, apellido, correo, hashed))

            else:
                flash("Tipo de usuario inválido", "danger")
                return redirect(url_for('registro'))

            conn.commit()
            flash(f"Registro de {tipo_usuario} completado. Ahora inicia sesión.", "success")
            return redirect(url_for('login'))

        except mysql.connector.IntegrityError as e:
            conn.rollback()
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for('registro'))

        except mysql.connector.Error as e:
            conn.rollback()
            flash(f"Error en la base de datos: {str(e)}", "danger")
            return redirect(url_for('registro'))

        finally:
            if conn:
                cur.close()
                conn.close()

    return render_template('Registrate.html')



@app.route('/contactanos', methods=['GET', 'POST'])
def contactanos():
    if request.method == 'POST':
        nombre = request.form.get('name', '').strip()
        correo = request.form.get('email', '').strip()
        telefono = request.form.get('phone', '').strip()
        asunto = request.form.get('subject', '').strip()
        mensaje = request.form.get('message', '').strip()
        if not nombre or not correo or not asunto or not mensaje:
            flash("Por favor completa los campos obligatorios.", "warning")
            return redirect(url_for('contactanos'))
        try:
            conn = get_connection()
            cursor = conn.cursor()
            sql = """INSERT INTO mensajes_contacto (nombre, correo, telefono, asunto, mensaje)VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (nombre, correo, telefono, asunto, mensaje))
            conn.commit()
            cursor.close()
            conn.close()
            flash("✅ Tu mensaje fue enviado correctamente.", "success")
            return redirect(url_for('contactanos'))
        except Exception as e:
            print("Error al guardar mensaje:", e)
            flash("❌ Ocurrió un error al enviar el mensaje.", "danger")
            return redirect(url_for('contactanos'))
    return render_template('contactanos.html')


@app.route('/terminos')
def terminos():
    """Términos y condiciones"""
  
    return render_template('terminos.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for('home'))

# ===========================================================
# 🧠 DASHBOARD DEL ORIENTADOR
# ===========================================================

@app.route('/orientador/dashboard')
@require_role('orientador')
def dashboard_orientador():
    """Dashboard principal del orientador con mensajes de contacto"""
    
    orientador_id = session.get('user_id') 
    conn = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # --- Datos estadísticos ---
        cur.execute("SELECT COUNT(*) as total FROM estudiantes")
        total_estudiantes = cur.fetchone()['total']
        
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM sesion_orientacion 
            WHERE orientador_id = %s
        """, (orientador_id,))
        total_sesiones = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM registro_inclusion")
        total_registros = cur.fetchone()['total']
        
        # --- Últimas sesiones ---
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

        # --- NUEVO: Mensajes de contacto ---
        cur.execute("""
            SELECT id, nombre, correo, telefono, asunto, mensaje
            FROM mensajes_contacto
            ORDER BY id DESC
        """)
        mensajes = cur.fetchall()

        cur.close()

        return render_template('orientador.html',
                               total_estudiantes=total_estudiantes,
                               total_sesiones=total_sesiones,
                               total_registros=total_registros,
                               ultimas_sesiones=ultimas_sesiones,
                               mensajes=mensajes)
        
    except mysql.connector.Error as e:
        flash(f"Error al cargar datos del dashboard: {str(e)}", "danger")
        return redirect(url_for('home'))
    finally:
        if conn:
            if 'cur' in locals() and cur:
                cur.close()
            conn.close()
            # ===========================================================
# 📩 GESTIÓN DE MENSAJES DE CONTACTO (CRUD)
# ===========================================================
@app.route('/orientador/eliminar_mensaje/<int:id>', methods=['POST'])
@require_role('orientador')
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

# ✅ LISTAR mensajes (READ)
@app.route('/orientador/mensajes')
@require_role('orientador')
def mensajes_orientador():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM mensajes_contacto ORDER BY id DESC")
    mensajes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('orientador_mensajes.html', mensajes=mensajes)

    # ✅ ACTUALIZAR estado (UPDATE)
@app.route('/orientador/mensajes/estado/<int:id>', methods=['POST'])
@require_role('orientador')
def actualizar_estado_mensaje(id):
    nuevo_estado = request.form.get('estado')
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE mensajes_contacto SET estado = %s WHERE id = %s", (nuevo_estado, id))
    conn.commit()
    cur.close()
    conn.close()
    flash("Estado actualizado ✅", "success")
    return redirect(url_for('mensajes_orientador'))

# ✅ ELIMINAR mensaje (DELETE)
@app.route('/orientador/mensajes/eliminar/<int:id>', methods=['POST'])
@require_role('orientador')
def eliminar_mensaje_orientador(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mensajes_contacto WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Mensaje eliminado ❌", "info")
    return redirect(url_for('mensajes_orientador'))
# ===========================================================
# 📄 REPORTES Y SUBIDA DE PDFS
# ===========================================================
@app.route('/orientador/reportes')
@require_role('orientador')
def orientador_reportes():
    return render_template('reportes.html')

@app.route('/orientador/reportes/guardar', methods=['POST'])
@require_role('orientador')
def guardar_reporte():
    orientador_id = session.get('user_id')
    titulo = request.form.get('titulo')
    tipo = request.form.get('tipo')
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

# ===========================================================
# 🧍‍♂️ DASHBOARD DE ACUDIENTE Y ESTUDIANTE
# ===========================================================

@app.route('/acudiente/dashboard')
@require_role('Acudiente')
def dashboard_acudiente():
    """Dashboard para el Acudiente. Mostrará información del estudiante a cargo."""
    nombre = session.get('user_nombre', 'Usuario')  # Recupera el nombre del acudiente desde la sesión
    return render_template('acudiente.html', nombre=nombre)

@app.route('/estudiante/dashboard')
@require_role('Estudiante')
def dashboard_estudiante():
    """Dashboard para el Estudiante. Mostrará sus sesiones y registros."""
    nombre = session.get('user_nombre', 'Usuario')  # Recupera el nombre del acudiente desde la sesión
    return render_template('estudiante.html', nombre=nombre)

# ============================================
# 📄 RUTAS PARA GENERAR PDFs
# ============================================
# ===========================================================
# 🧾 GENERACIÓN DE REPORTES EN PDF
# ===========================================================
@app.route('/orientador/reportes/estudiantes')
@require_role('orientador')
def reporte_estudiantes_pdf():
    """Descargar reporte de estudiantes en PDF"""
    orientador_id = session.get('user_id')
    
    try:
        pdf_data = generar_pdf_estudiantes(orientador_id)
        
        if pdf_data:
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=reporte_estudiantes_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            flash("Error al generar el reporte", "danger")
            return redirect('/orientador/reportes')
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger")
        return redirect('/orientador/reportes')


@app.route('/orientador/reportes/sesiones')
@require_role('orientador')
def reporte_sesiones_pdf():
    """Descargar reporte de sesiones en PDF"""
    orientador_id = session.get('user_id')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    try:
        pdf_data = generar_pdf_sesiones(orientador_id, fecha_inicio, fecha_fin)
        
        if pdf_data:
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=reporte_sesiones_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            flash("Error al generar el reporte", "danger")
            return redirect('/orientador/reportes')
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger")
        return redirect('/orientador/reportes')


@app.route('/orientador/reportes/completo')
@require_role('orientador')
def reporte_completo_pdf():
    """Descargar reporte completo"""
    orientador_id = session.get('user_id')
    
    try:
        pdf = PDF_Reporte(titulo='Reporte Completo de Orientación')
        pdf.alias_nb_pages()
        pdf.add_page()
        
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
        estudiantes = cur.fetchall()
        
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(10, 8, 'ID', 1, 0, 'C')
        pdf.cell(70, 8, 'Nombre', 1, 0, 'C')
        pdf.cell(20, 8, 'Edad', 1, 0, 'C')
        pdf.cell(50, 8, 'Grado', 1, 0, 'C')
        pdf.cell(30, 8, 'Promedio', 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for est in estudiantes:
            pdf.cell(10, 7, str(est['id']), 1, 0, 'C')
            pdf.cell(70, 7, est['nombre_completo'][:35], 1, 0, 'L')
            pdf.cell(20, 7, str(est['edad'] or 'N/A'), 1, 0, 'C')
            pdf.cell(50, 7, est['grado'][:25] or 'N/A', 1, 0, 'L')
            pdf.cell(30, 7, str(est['promedio']), 1, 0, 'C')
            pdf.ln()
        
        pdf.ln(10)
        
        # SECCIÓN SESIONES
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'SESIONES RECIENTES', 0, 1, 'L')
        pdf.ln(5)
        
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
        sesiones = cur.fetchall()
        
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(25, 8, 'Fecha', 1, 0, 'C')
        pdf.cell(25, 8, 'Hora', 1, 0, 'C')
        pdf.cell(60, 8, 'Estudiante', 1, 0, 'C')
        pdf.cell(30, 8, 'Tipo', 1, 0, 'C')
        pdf.cell(40, 8, 'Descripción', 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font('Arial', '', 8)
        for ses in sesiones:
            pdf.cell(25, 7, ses['fecha'].strftime('%d/%m/%Y'), 1, 0, 'C')
            pdf.cell(25, 7, ses['hora_inicio'].strftime('%H:%M'), 1, 0, 'C')
            pdf.cell(60, 7, ses['estudiante'][:30], 1, 0, 'L')
            pdf.cell(30, 7, ses['tipo_sesion'], 1, 0, 'C')
            pdf.cell(40, 7, (ses['descripcion'] or 'N/A')[:20], 1, 0, 'L')
            pdf.ln()
        
        cur.close()
        conn.close()
        
        pdf_data = pdf.output(dest='S').encode('latin-1')
        
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=reporte_completo_{datetime.now().strftime("%Y%m%d")}.pdf'
        return response
        
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect('/orientador/reportes')
 
# ===========================================================
#  EJECUCIÓN DEL SERVIDOR LOCAL, en  caso de que se haya dado bien la identificación de las importaciones y de las diferentes librerias
# ===========================================================
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
