from flask import Flask, render_template, request, redirect, url_for, jsonify
from pyzbar.pyzbar import decode
import cv2
import base64
import numpy as np
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('instance/carros.db')
    conn.row_factory = sqlite3.Row
    return conn

# Asegurarse de que existe el directorio para la base de datos
if not os.path.exists('instance'):
    os.makedirs('instance')

# Función para inicializar la base de datos
def init_db():
    conn = sqlite3.connect('instance/carros.db')
    c = conn.cursor()
    
    
    # Tabla para registros de autos
    c.execute('''
        CREATE TABLE IF NOT EXISTS RegistrosAutos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT,
            nombre_tecnico TEXT,
            ultimo_mantenimiento TIMESTAMP,
            salida TIMESTAMP,
            regreso TIMESTAMP
        )
    ''')
    
    # Tabla para checklist
    c.execute('''
        CREATE TABLE IF NOT EXISTS CheckListAutos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_coche TEXT,
            observaciones TEXT,
            kilometraje TEXT,
            luces BOOLEAN,
            antena BOOLEAN,
            espejo_derecho BOOLEAN,
            espejo_izquierdo BOOLEAN,
            cristales BOOLEAN,
            emblema BOOLEAN,
            llantas BOOLEAN,
            tapon_gasolina BOOLEAN,
            carroceria_sin_golpes BOOLEAN,
            claxon BOOLEAN,
            instrumentos_tablero BOOLEAN,
            clima BOOLEAN,
            limpiadores BOOLEAN,
            bocinas BOOLEAN,
            espejo_retrovisor BOOLEAN,
            cinturones BOOLEAN,
            botones_interiores BOOLEAN,
            manijas_interiores BOOLEAN,
            tapetes BOOLEAN,
            vestiduras BOOLEAN,
            gato BOOLEAN,
            maneral_gato BOOLEAN,
            llave_ruedas BOOLEAN,
            refacciones BOOLEAN,
            herramientas BOOLEAN,
            extintor BOOLEAN,
            aceite BOOLEAN,
            anticongelante BOOLEAN,
            liquido_frenos BOOLEAN,
            tarjeta_circulacion BOOLEAN,
            papeles_seguro BOOLEAN,
            licencia_vigente BOOLEAN,
            ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al arrancar la aplicación
init_db()

def get_db_connection():
    conn = sqlite3.connect('instance/carros.db')
    conn.row_factory = sqlite3.Row
    return conn

def registrar_salida_regreso(qr_code, nombre_tecnico, ultimo_mantenimiento, accion):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            ultimo_mantenimiento_dt = datetime.fromisoformat(ultimo_mantenimiento)
        except ValueError as e:
            print(f"Formato de fecha incorrecto en 'ultimo_mantenimiento': {e}")
            return False

        print(f"Registrando con QR code: {qr_code}, Acción: {accion}")

        cursor.execute("SELECT id, salida, regreso FROM RegistrosAutos WHERE qr_code = ?", (qr_code,))
        registro_existente = cursor.fetchone()

        if registro_existente:
            if accion == "Salida":
                cursor.execute("""
                    UPDATE RegistrosAutos 
                    SET salida = ?, nombre_tecnico = ?, ultimo_mantenimiento = ? 
                    WHERE qr_code = ?
                """, (datetime.now(), nombre_tecnico, ultimo_mantenimiento_dt, qr_code))
            elif accion == "Regreso":
                cursor.execute("""
                    UPDATE RegistrosAutos 
                    SET regreso = ?, nombre_tecnico = ?, ultimo_mantenimiento = ? 
                    WHERE qr_code = ?
                """, (datetime.now(), nombre_tecnico, ultimo_mantenimiento_dt, qr_code))
        else:
            if accion == "Salida":
                cursor.execute("""
                    INSERT INTO RegistrosAutos (qr_code, nombre_tecnico, ultimo_mantenimiento, salida)
                    VALUES (?, ?, ?, ?)
                """, (qr_code, nombre_tecnico, ultimo_mantenimiento_dt, datetime.now()))
            else:
                print(f"No se puede registrar regreso sin salida para QR: {qr_code}")
                return False

        conn.commit()
        print("Datos guardados correctamente")
        return True
    except Exception as e:
        print(f"Error general en registrar_salida_regreso: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    registros = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM RegistrosAutos ORDER BY id DESC LIMIT 1000")
        registros = cursor.fetchall()
    except Exception as e:
        print(f"Error al consultar la base de datos en index: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    if request.method == 'POST':
        nombre_tecnico = request.form['nombre_tecnico']
        ultimo_mantenimiento = request.form['ultimo_mantenimiento']
        qr_data = request.form['qr_data']
        accion = request.form['accion']

        if qr_data and registrar_salida_regreso(qr_data, nombre_tecnico, ultimo_mantenimiento, accion):
            return redirect(url_for('confirmacion', qr_data=qr_data, nombre_tecnico=nombre_tecnico, accion=accion))
        else:
            return "Error en el registro"

    return render_template('index.html', registros=registros)

@app.route('/lista')
def lista():
    registros = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM RegistrosAutos ORDER BY id DESC")
        registros = cursor.fetchall()
    except Exception as e:
        print(f"Error al consultar la base de datos en lista: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

    return render_template('lista.html', registros=registros)

@app.route('/confirmacion')
def confirmacion():
    qr_data = request.args.get('qr_data')
    nombre_tecnico = request.args.get('nombre_tecnico')
    accion = request.args.get('accion')
    return render_template('confirmacion.html', qr_data=qr_data, nombre_tecnico=nombre_tecnico, accion=accion)

@app.route('/escaneo_qr', methods=['POST'])
def escaneo_qr():
    data = request.json
    image_base64 = data['image']
    qr_data = procesar_imagen_qr(image_base64)

    if qr_data:
        return jsonify({'success': True, 'qr_data': qr_data})
    else:
        return jsonify({'success': False, 'message': 'No se detectó ningún QR'})

def procesar_imagen_qr(image_base64):
    image_data = base64.b64decode(image_base64)
    np_arr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    decoded_objects = decode(img)
    for obj in decoded_objects:
        qr_data = obj.data.decode('utf-8')
        return qr_data
    return None

@app.route('/verificar_qr', methods=['POST'])
def verificar_qr():
    data = request.json
    qr_code = data['qr_data']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre_tecnico, ultimo_mantenimiento 
            FROM RegistrosAutos 
            WHERE qr_code = ?
        """, (qr_code,))
        resultado = cursor.fetchone()

        if resultado:
            nombre_tecnico, ultimo_mantenimiento = resultado
            return jsonify({
                'exists': True,
                'nombre_tecnico': nombre_tecnico,
                'ultimo_mantenimiento': ultimo_mantenimiento
            })
        else:
            return jsonify({'exists': False})

    except Exception as e:
        print(f"Error al verificar QR en la base de datos: {e}")
        return jsonify({'error': 'Error al verificar QR'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/checklist', methods=['GET', 'POST'])
def checklist():
    if request.method == 'POST':
        numero_coche = request.form['numero_coche']
        kilometraje = request.form['kilometraje']
        observaciones = request.form['observaciones']
        
        campos = ['luces', 'antena', 'espejo_derecho', 'espejo_izquierdo', 'cristales', 
                 'emblema', 'llantas', 'tapon_gasolina', 'carroceria_sin_golpes', 'claxon',
                 'instrumentos_tablero', 'clima', 'limpiadores', 'bocinas', 'espejo_retrovisor',
                 'cinturones', 'botones_interiores', 'manijas_interiores', 'tapetes', 'vestiduras',
                 'gato', 'maneral_gato', 'llave_ruedas', 'refacciones', 'herramientas', 'extintor',
                 'aceite', 'anticongelante', 'liquido_frenos', 'tarjeta_circulacion',
                 'papeles_seguro', 'licencia_vigente']
        
        valores = {campo: request.form.get(campo, '0') == '1' for campo in campos}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verificar si existe el registro
            cursor.execute("SELECT 1 FROM CheckListAutos WHERE numero_coche = ?", (numero_coche,))
            existe = cursor.fetchone()
            
            if existe:
                # Actualizar registro existente
                set_clause = ', '.join([f"{campo} = ?" for campo in ['kilometraje', 'observaciones'] + campos])
                query = f"UPDATE CheckListAutos SET {set_clause}, ultima_actualizacion = CURRENT_TIMESTAMP WHERE numero_coche = ?"
                valores_update = [kilometraje, observaciones] + [valores[campo] for campo in campos] + [numero_coche]
                cursor.execute(query, valores_update)
            else:
                # Insertar nuevo registro
                campos_sql = ['numero_coche', 'kilometraje', 'observaciones'] + campos
                placeholders = ','.join(['?' for _ in campos_sql])
                query = f"INSERT INTO CheckListAutos ({','.join(campos_sql)}) VALUES ({placeholders})"
                valores_insert = [numero_coche, kilometraje, observaciones] + [valores[campo] for campo in campos]
                cursor.execute(query, valores_insert)
            
            conn.commit()
            return redirect(url_for('checklist', message="Checklist actualizado correctamente"))
        except Exception as e:
            print(f"Error al actualizar el checklist: {e}")
            return redirect(url_for('checklist', error="Error al actualizar el checklist"))
        finally:
            if 'conn' in locals():
                conn.close()
    

    coches = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT numero_coche FROM CheckListAutos")
        coches = [row['numero_coche'] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error al obtener la lista de coches: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return render_template('checklist.html', coches=coches, 
                         message=request.args.get('message'), 
                         error=request.args.get('error'))

@app.route('/get_car_details/<string:numero_coche>')
def get_car_details(numero_coche):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM CheckListAutos WHERE numero_coche = ?
        """, (numero_coche,))
        car = cursor.fetchone()
        
        if car:
            car_dict = dict(car)
            # Convertir valores booleanos de SQLite (0/1) a Python (True/False)
            for key in car_dict:
                if isinstance(car_dict[key], int) and key not in ['id']:
                    car_dict[key] = bool(car_dict[key])
            return jsonify(car_dict)
        else:
            return jsonify({"error": "Coche no encontrado"}), 404
    except Exception as e:
        print(f"Error al obtener detalles del coche: {e}")
        return jsonify({"error": "Error al obtener detalles del coche"}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_registro(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminar el registro de RegistrosAutos
        cursor.execute("DELETE FROM RegistrosAutos WHERE id = ?", (id,))
        
        # Eliminar el registro de CheckListAutos si existe
        cursor.execute("DELETE FROM CheckListAutos WHERE id = ?", (id,))
        
        conn.commit()
        return redirect(url_for('lista'))
    except Exception as e:
        print(f"Error al eliminar el registro: {e}")
        return "Error al eliminar el registro", 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/eliminar_checklist/<string:numero_coche>', methods=['POST'])
def eliminar_checklist(numero_coche):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminar el registro de CheckListAutos
        cursor.execute("DELETE FROM CheckListAutos WHERE numero_coche = ?", (numero_coche,))
        
        conn.commit()
        return redirect(url_for('checklist', message="Checklist eliminado correctamente"))
    except Exception as e:
        print(f"Error al eliminar el checklist: {e}")
        return redirect(url_for('checklist', error="Error al eliminar el checklist"))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)