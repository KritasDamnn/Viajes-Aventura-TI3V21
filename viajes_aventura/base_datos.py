"""
base_datos.py
Conexión a la base de datos SQLite y creación de las tablas.
(Paso 4 - Persistencia de datos)
"""
import os
import sqlite3

# La base de datos se guarda en un archivo junto al programa
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viajes_aventura.db")


def conectar():
    """Abre una conexión a la base de datos."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row            # permite usar fila["nombre"]
    conexion.execute("PRAGMA foreign_keys = ON")  # activa las llaves foráneas
    return conexion


def ejecutar(sql, parametros=()):
    """Ejecuta INSERT / UPDATE / DELETE. Devuelve el id de la última fila creada."""
    conexion = conectar()
    try:
        cursor = conexion.execute(sql, parametros)
        conexion.commit()
        return cursor.lastrowid
    finally:
        conexion.close()


def consultar(sql, parametros=()):
    """Ejecuta un SELECT y devuelve la lista de filas."""
    conexion = conectar()
    try:
        return conexion.execute(sql, parametros).fetchall()
    finally:
        conexion.close()


def crear_tablas():
    """Crea las tablas si todavía no existen."""
    conexion = conectar()
    try:
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL CHECK (rol IN ('cliente', 'admin'))
            );

            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                pais TEXT NOT NULL,
                costo REAL NOT NULL CHECK (costo > 0)
            );

            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                cupos INTEGER NOT NULL CHECK (cupos >= 0),
                ida_y_vuelta INTEGER NOT NULL DEFAULT 0,   -- 1 = ida y vuelta, 0 = solo ida
                fecha_vuelta TEXT,                         -- solo si es ida y vuelta
                hora_vuelo TEXT                            -- hora del vuelo (HH:MM)
            );

            -- Tabla intermedia: un paquete tiene varios destinos
            CREATE TABLE IF NOT EXISTS paquete_destinos (
                paquete_id INTEGER NOT NULL,
                destino_id INTEGER NOT NULL,
                PRIMARY KEY (paquete_id, destino_id),
                FOREIGN KEY (paquete_id) REFERENCES paquetes(id) ON DELETE CASCADE,
                FOREIGN KEY (destino_id) REFERENCES destinos(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                paquete_id INTEGER NOT NULL,
                personas INTEGER NOT NULL CHECK (personas > 0),
                total REAL NOT NULL,
                fecha_reserva TEXT NOT NULL,
                estado TEXT NOT NULL CHECK (estado IN ('confirmada', 'cancelada')),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (paquete_id) REFERENCES paquetes(id)
            );
        """)
        conexion.commit()
        _actualizar_bd_antigua(conexion)
    finally:
        conexion.close()


def _actualizar_bd_antigua(conexion):
    """Si la base de datos fue creada con una versión anterior, la adapta a la nueva."""
    columnas = [f[1] for f in conexion.execute("PRAGMA table_info(paquetes)")]
    for nombre, definicion in (("ida_y_vuelta", "INTEGER NOT NULL DEFAULT 0"),
                               ("fecha_vuelta", "TEXT"),
                               ("hora_vuelo", "TEXT")):
        if nombre not in columnas:
            conexion.execute(f"ALTER TABLE paquetes ADD COLUMN {nombre} {definicion}")
    # La columna 'descripcion' de destinos ya no se usa
    columnas = [f[1] for f in conexion.execute("PRAGMA table_info(destinos)")]
    if "descripcion" in columnas:
        conexion.execute("ALTER TABLE destinos DROP COLUMN descripcion")
    conexion.commit()


def renumerar(tabla, tablas_hijas=()):
    """Reordena los ID de una tabla para que queden 1, 2, 3... sin vacíos.

    Se usa después de eliminar un registro. 'tablas_hijas' es una lista de
    (tabla, columna) que guardan ese ID como llave foránea; también se actualizan
    para que las relaciones no se rompan.
    (tabla y columnas son nombres fijos escritos en el código, nunca datos del usuario)
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.execute("PRAGMA foreign_keys = OFF")   # se apaga solo mientras se reordena
    try:
        ids = [f[0] for f in conexion.execute(f"SELECT id FROM {tabla} ORDER BY id")]
        for nuevo, viejo in enumerate(ids, start=1):
            if nuevo != viejo:
                conexion.execute(f"UPDATE {tabla} SET id = ? WHERE id = ?", (nuevo, viejo))
                for tabla_hija, columna in tablas_hijas:
                    conexion.execute(
                        f"UPDATE {tabla_hija} SET {columna} = ? WHERE {columna} = ?", (nuevo, viejo))
        # El próximo registro nuevo continúa desde el último ID
        conexion.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = ?", (len(ids), tabla))
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
