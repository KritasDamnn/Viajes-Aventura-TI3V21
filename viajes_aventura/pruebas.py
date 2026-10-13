"""
pruebas.py
Pruebas automáticas básicas. Ejecutar con:  python pruebas.py
Usan una base de datos temporal, así que NO tocan viajes_aventura.db.
"""
import os
import tempfile
import unittest
from datetime import date, timedelta

import autenticacion
import base_datos
import seguridad
from gestores import GestorDestinos, GestorPaquetes, GestorReservas
from modelos import Administrador

CLAVE = "Clave#Segura1"


class PruebasSistema(unittest.TestCase):

    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        archivo.close()
        self.ruta = archivo.name
        base_datos.RUTA_BD = self.ruta
        base_datos.crear_tablas()
        autenticacion._guardar_usuario("Admin", "admin@viajes.cl", CLAVE, "admin")
        autenticacion.registrar_cliente("Ana", "ana@correo.cl", CLAVE)
        self.admin = autenticacion.iniciar_sesion("admin@viajes.cl", CLAVE)
        self.cliente = autenticacion.iniciar_sesion("ana@correo.cl", CLAVE)
        self.destinos = GestorDestinos()
        self.paquetes = GestorPaquetes()
        self.reservas = GestorReservas()

    def tearDown(self):
        os.unlink(self.ruta)

    def _paquete(self, cupos=5):
        d1 = self.destinos.registrar(self.admin, "Atacama", "Chile", 100000)
        d2 = self.destinos.registrar(self.admin, "Cusco", "Peru", 200000)
        inicio = (date.today() + timedelta(days=10)).isoformat()
        fin = (date.today() + timedelta(days=15)).isoformat()
        return self.paquetes.crear(self.admin, "Ruta Andina", inicio, fin, cupos, [d1, d2])

    # --- seguridad
    def test_password_no_se_guarda_en_texto_plano(self):
        fila = base_datos.consultar("SELECT password_hash FROM usuarios WHERE email = 'ana@correo.cl'")[0]
        self.assertNotIn(CLAVE, fila["password_hash"])

    def test_dos_hash_distintos_para_misma_clave(self):
        self.assertNotEqual(seguridad.hashear_password(CLAVE), seguridad.hashear_password(CLAVE))

    def test_password_debil_rechazada(self):
        with self.assertRaises(ValueError):
            autenticacion.registrar_cliente("Luis", "luis@correo.cl", "abc")

    def test_login_incorrecto(self):
        with self.assertRaises(ValueError):
            autenticacion.iniciar_sesion("ana@correo.cl", "OtraClave1!")
        with self.assertRaises(ValueError):
            autenticacion.iniciar_sesion("noexiste@correo.cl", CLAVE)

    def test_correo_duplicado(self):
        with self.assertRaises(ValueError):
            autenticacion.registrar_cliente("Ana 2", "ana@correo.cl", CLAVE)

    def test_sql_injection_no_funciona(self):
        with self.assertRaises(ValueError):
            autenticacion.iniciar_sesion("' OR '1'='1", "x")

    def test_cliente_no_puede_crear_destino(self):
        with self.assertRaises(PermissionError):
            self.destinos.registrar(self.cliente, "Roma", "Italia", 500000)

    # --- destinos (CRUD)
    def test_crud_destinos(self):
        id_ = self.destinos.registrar(self.admin, "Roma", "Italia", 500000)
        self.assertEqual(self.destinos.buscar(id_).pais, "Italia")
        self.destinos.modificar(self.admin, id_, costo="600000")
        self.assertEqual(self.destinos.buscar(id_).costo, 600000)
        self.destinos.eliminar(self.admin, id_)
        self.assertIsNone(self.destinos.buscar(id_))

    def test_destino_costo_invalido(self):
        with self.assertRaises(ValueError):
            self.destinos.registrar(self.admin, "Roma", "Italia", "-5")
        with self.assertRaises(ValueError):
            self.destinos.registrar(self.admin, "Roma", "Italia", "abc")

    def test_no_eliminar_destino_en_paquete(self):
        self._paquete()
        with self.assertRaises(ValueError):
            self.destinos.eliminar(self.admin, self.destinos.listar()[0].id)

    # --- paquetes
    def test_paquete_necesita_2_destinos(self):
        d1 = self.destinos.registrar(self.admin, "Roma", "Italia", 500000)
        inicio = (date.today() + timedelta(days=5)).isoformat()
        with self.assertRaises(ValueError):
            self.paquetes.crear(self.admin, "Solo uno", inicio, inicio, 5, [d1])

    def test_fechas_invalidas(self):
        d1 = self.destinos.registrar(self.admin, "Roma", "Italia", 500000)
        d2 = self.destinos.registrar(self.admin, "Paris", "Francia", 600000)
        with self.assertRaises(ValueError):
            self.paquetes.crear(self.admin, "Pasado", "2020-01-01", "2020-01-05", 5, [d1, d2])
        with self.assertRaises(ValueError):
            self.paquetes.crear(self.admin, "Mal", "10-10-2030", "2030-10-12", 5, [d1, d2])

    def test_calculo_de_costo(self):
        id_ = self._paquete()
        self.assertEqual(self.paquetes.calcular_costo(id_, 2), 600000)

    def test_modificar_paquete(self):
        id_ = self._paquete()
        self.paquetes.modificar(self.admin, id_, cupos="9")
        self.assertEqual(self.paquetes.buscar(id_).cupos, 9)

    # --- vuelo (ida / ida y vuelta y hora)
    def _dos_destinos(self):
        return [self.destinos.registrar(self.admin, "Roma", "Italia", 500000),
                self.destinos.registrar(self.admin, "Paris", "Francia", 600000)]

    def test_paquete_ida_y_vuelta_con_hora(self):
        ids = self._dos_destinos()
        ini = (date.today() + timedelta(days=10)).isoformat()
        fin = (date.today() + timedelta(days=15)).isoformat()
        id_ = self.paquetes.crear(self.admin, "Europa", ini, fin, 5, ids, True, fin, "08:30")
        p = self.paquetes.buscar(id_)
        self.assertTrue(p.ida_y_vuelta)
        self.assertEqual((p.fecha_vuelta, p.hora_vuelo), (fin, "08:30"))
        self.assertIn("ida y vuelta", p.mostrar())

    def test_paquete_solo_ida_no_guarda_fecha_vuelta(self):
        ids = self._dos_destinos()
        ini = (date.today() + timedelta(days=10)).isoformat()
        fin = (date.today() + timedelta(days=15)).isoformat()
        id_ = self.paquetes.crear(self.admin, "Europa", ini, fin, 5, ids, False, fin, "21:05")
        p = self.paquetes.buscar(id_)
        self.assertFalse(p.ida_y_vuelta)
        self.assertIsNone(p.fecha_vuelta)

    def test_ida_y_vuelta_exige_fecha_y_hora_valida(self):
        ids = self._dos_destinos()
        ini = (date.today() + timedelta(days=10)).isoformat()
        fin = (date.today() + timedelta(days=15)).isoformat()
        with self.assertRaises(ValueError):      # falta la fecha de vuelta
            self.paquetes.crear(self.admin, "E1", ini, fin, 5, ids, True, None, "08:30")
        with self.assertRaises(ValueError):      # vuelta antes de la ida
            self.paquetes.crear(self.admin, "E2", ini, fin, 5, ids, True, date.today().isoformat(), "08:30")
        with self.assertRaises(ValueError):      # hora inválida
            self.paquetes.crear(self.admin, "E3", ini, fin, 5, ids, False, None, "25:99")

    def test_bd_antigua_se_actualiza(self):
        import sqlite3
        con = sqlite3.connect(self.ruta)
        con.executescript("""DROP TABLE reservas; DROP TABLE paquete_destinos; DROP TABLE paquetes;
            DROP TABLE destinos;
            CREATE TABLE destinos (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
              pais TEXT NOT NULL, descripcion TEXT NOT NULL, costo REAL NOT NULL);
            INSERT INTO destinos (nombre, pais, descripcion, costo) VALUES ('Lima','Peru','x',1000);
            CREATE TABLE paquetes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE,
              fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL, cupos INTEGER NOT NULL);""")
        con.commit()
        con.close()
        base_datos.crear_tablas()
        self.assertEqual(len(self.destinos.listar()), 1)
        self.destinos.registrar(self.admin, "Quito", "Ecuador", 2000)

    # --- reservas
    def test_reservar_descuenta_cupos(self):
        id_ = self._paquete(cupos=5)
        self.reservas.reservar(self.cliente, id_, 2)
        self.assertEqual(self.paquetes.buscar(id_).cupos, 3)
        historial = self.reservas.historial(self.cliente)
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].total, 600000)

    def test_reservar_sin_cupos(self):
        id_ = self._paquete(cupos=2)
        with self.assertRaises(ValueError):
            self.reservas.reservar(self.cliente, id_, 3)

    def test_cancelar_devuelve_cupos(self):
        id_ = self._paquete(cupos=5)
        reserva = self.reservas.reservar(self.cliente, id_, 2)
        self.reservas.cancelar(self.cliente, reserva)
        self.assertEqual(self.paquetes.buscar(id_).cupos, 5)
        with self.assertRaises(ValueError):
            self.reservas.cancelar(self.cliente, reserva)

    def test_no_cancelar_reserva_ajena(self):
        id_ = self._paquete()
        reserva = self.reservas.reservar(self.cliente, id_, 1)
        autenticacion.registrar_cliente("Beto", "beto@correo.cl", CLAVE)
        otro = autenticacion.iniciar_sesion("beto@correo.cl", CLAVE)
        with self.assertRaises(PermissionError):
            self.reservas.cancelar(otro, reserva)

    def test_admin_ve_todas_las_reservas(self):
        id_ = self._paquete()
        self.reservas.reservar(self.cliente, id_, 1)
        self.assertEqual(len(self.reservas.historial(self.admin)), 1)

    def test_admin_no_reserva(self):
        id_ = self._paquete()
        with self.assertRaises(PermissionError):
            self.reservas.reservar(self.admin, id_, 1)

    def test_modificar_personas_ajusta_cupos_y_total(self):
        id_ = self._paquete(cupos=5)
        reserva = self.reservas.reservar(self.cliente, id_, 2)        # quedan 3
        self.reservas.modificar_personas(self.cliente, reserva, 4)    # quedan 1
        self.assertEqual(self.paquetes.buscar(id_).cupos, 1)
        self.assertEqual(self.reservas.buscar(reserva).total, 1200000)
        self.reservas.modificar_personas(self.cliente, reserva, 1)    # devuelve cupos
        self.assertEqual(self.paquetes.buscar(id_).cupos, 4)
        with self.assertRaises(ValueError):
            self.reservas.modificar_personas(self.cliente, reserva, 10)  # no hay cupos

    def test_eliminar_reserva_solo_cancelada(self):
        id_ = self._paquete()
        reserva = self.reservas.reservar(self.cliente, id_, 1)
        with self.assertRaises(ValueError):
            self.reservas.eliminar(self.admin, reserva)
        with self.assertRaises(PermissionError):
            self.reservas.eliminar(self.cliente, reserva)
        self.reservas.cancelar(self.cliente, reserva)
        self.reservas.eliminar(self.admin, reserva)
        self.assertIsNone(self.reservas.buscar(reserva))

    def test_id_se_renumeran_al_eliminar(self):
        # Destinos 1,2,3 -> se elimina el 2 -> quedan 1,2 y el siguiente nuevo es el 3
        a = self.destinos.registrar(self.admin, "Roma", "Italia", 500000)
        b = self.destinos.registrar(self.admin, "Paris", "Francia", 600000)
        c = self.destinos.registrar(self.admin, "Lima", "Peru", 300000)
        self.destinos.eliminar(self.admin, b)
        ids = sorted(d.id for d in self.destinos.listar())
        self.assertEqual(ids, [1, 2])
        self.assertEqual(self.destinos.buscar(2).nombre, "Lima")
        nuevo = self.destinos.registrar(self.admin, "Quito", "Ecuador", 200000)
        self.assertEqual(nuevo, 3)

    def test_renumerar_mantiene_relaciones(self):
        # Se eliminan paquetes del medio; las reservas y destinos del paquete siguen enlazados
        d = [self.destinos.registrar(self.admin, n, "Chile", 1000) for n in ("A1", "B2", "C3")]
        inicio = (date.today() + timedelta(days=10)).isoformat()
        fin = (date.today() + timedelta(days=12)).isoformat()
        p1 = self.paquetes.crear(self.admin, "Uno", inicio, fin, 5, [d[0], d[1]])
        p2 = self.paquetes.crear(self.admin, "Dos", inicio, fin, 5, [d[1], d[2]])
        p3 = self.paquetes.crear(self.admin, "Tres", inicio, fin, 5, [d[0], d[2]])
        reserva = self.reservas.reservar(self.cliente, p3, 2)
        self.paquetes.eliminar(self.admin, p2)
        self.assertEqual(sorted(p.id for p in self.paquetes.listar()), [1, 2])
        tres = self.paquetes.buscar(2)
        self.assertEqual(tres.nombre, "Tres")
        self.assertEqual(sorted(x.nombre for x in tres.destinos), ["A1", "C3"])
        self.assertEqual(self.reservas.buscar(reserva).paquete_id, 2)

    def test_persistencia_en_archivo(self):
        self._paquete()
        # Se vuelve a leer desde la base de datos con un gestor nuevo
        self.assertEqual(len(GestorPaquetes().listar()), 1)
        self.assertIsInstance(self.admin, Administrador)


if __name__ == "__main__":
    unittest.main(verbosity=2)
