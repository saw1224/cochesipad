import pyodbc
import sqlite3
from datetime import datetime

def migrate_data():
    # Conexión a SQL Server (ajusta estos valores según tu configuración anterior)
    sql_server_conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=DESKTOP-1F9VP1F\SQLEXPRESS;DATABASE=carrosISI;UID=saa;PWD=12345'
    )
    
    # Conexión a SQLite
    sqlite_conn = sqlite3.connect('instance/carros.db')
    
    try:
        # Migrar RegistrosAutos
        print("Migrando RegistrosAutos...")
        sql_cursor = sql_server_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()
        
        sql_cursor.execute("SELECT * FROM RegistrosAutos")
        registros = sql_cursor.fetchall()
        
        for registro in registros:
            sqlite_cursor.execute("""
                INSERT INTO RegistrosAutos (id, qr_code, nombre_tecnico, ultimo_mantenimiento, salida, regreso)
                VALUES (?, ?, ?, ?, ?, ?)
            """, registro)
        
        # Migrar CheckListAutos
        print("Migrando CheckListAutos...")
        sql_cursor.execute("SELECT * FROM CheckListAutos")
        checklists = sql_cursor.fetchall()
        
        for checklist in checklists:
            sqlite_cursor.execute("""
                INSERT INTO CheckListAutos (
                    id, numero_coche, kilometraje, luces, antena, espejo_derecho,
                    espejo_izquierdo, cristales, emblema, llantas, tapon_gasolina,
                    carroceria_sin_golpes, claxon, instrumentos_tablero, clima,
                    limpiadores, bocinas, espejo_retrovisor, cinturones,
                    botones_interiores, manijas_interiores, tapetes, vestiduras,
                    gato, maneral_gato, llave_ruedas, refacciones, herramientas,
                    extintor, aceite, anticongelante, liquido_frenos,
                    tarjeta_circulacion, papeles_seguro, licencia_vigente,
                    ultima_actualizacion
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, checklist)
        
        sqlite_conn.commit()
        print("Migración completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        sqlite_conn.rollback()
    finally:
        sql_server_conn.close()
        sqlite_conn.close()

if __name__ == "__main__":
    migrate_data()