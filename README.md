Este archivo .PY consiste en un proyecto para la doceava evaluación, "Desarrollo de Soluciones de Software en Python
". Se debe descargar el archivo y ejecutar mediante Visual Studio Code

Esta evaluación universitaria fue hecha por; 
Diego Benjamín Soto Valenzuela, Felipe Ignacio Inostroza Retamal y Sebastián Alexis Soto Sanhueza

Los tres pertenecientes a la clase asignada como "TI3V21".

CÓMO EJECUTAR (Python 3.10 o superior, no hay que instalar nada)
    python main.py          -> abre el sistema
    python pruebas.py       -> corre las 29 pruebas automáticas

La primera vez el sistema pide crear al administrador (contraseña: 8+ caracteres con
mayúscula, minúscula, número y símbolo). La base de datos viajes_aventura.db se crea sola.

------------------------------------------------------------------------------
QUÉ HACE CADA ARCHIVO .py  (y a qué paso/criterio de la guía corresponde)
------------------------------------------------------------------------------
main.py              Punto de entrada. Crea la BD, el admin inicial y abre el menú.

--- Clases (Paso 2 diagrama de clases / Paso 4 POO) - criterios 4.1.2 y 4.1.4
modelos.py           Usuario, Cliente, Administrador (HERENCIA + POLIMORFISMO), Destino,
                     Paquete (tiene varios Destinos; calcula costo y disponibilidad) y Reserva

--- Persistencia y CRUD (Paso 4) - criterio 4.1.4
base_datos.py        Conexión SQLite y creación de las 5 tablas
gestores.py          GestorDestinos (CRUD de destinos), GestorPaquetes (CRUD de paquetes,
                     disponibilidad, cálculo de costos) y GestorReservas (reservar, historial,
                     cancelar: descuenta/devuelve cupos)

--- Seguridad (Paso 5) - criterio 4.1.5
seguridad.py         Hash scrypt + sal (hashlib, secrets, hmac), política de contraseña, permisos por rol
autenticacion.py     Registro, admin inicial, login con mensaje de error genérico
validaciones.py      Validación de todos los datos ingresados (lista blanca)

--- Interfaz
menus.py             Menú principal, de cliente y de administrador

pruebas.py           Pruebas automáticas (evidencia de calidad)

------------------------------------------------------------------------------
CRUD SOBRE SQLITE (base_datos.py -> archivo viajes_aventura.db)
------------------------------------------------------------------------------
                 Crear (INSERT)   Leer (SELECT)        Actualizar (UPDATE)     Eliminar (DELETE)
                 
Destinos         registrar        listar / buscar      modificar               eliminar

Paquetes         crear            listar / buscar      modificar               eliminar

Reservas         reservar         historial / buscar   modificar_personas      eliminar (solo canceladas)

Usuarios         registrar        iniciar_sesion       (no aplica)             (no aplica)

Además, cancelar una reserva hace UPDATE del estado y devuelve los cupos.

------------------------------------------------------------------------------
REQUERIMIENTOS DE LA GUÍA vs. DÓNDE SE CUMPLEN
------------------------------------------------------------------------------
Registrar / modificar / eliminar / listar destinos ..... gestores.py
Crear paquetes con múltiples destinos ................... gestores.py (mínimo 2 destinos)

Definir fechas y costos ................................. gestores.py + modelos.py

Consultar disponibilidad de paquetes .................... GestorPaquetes.listar(solo_disponibles=True)

Calcular costos según destinos .......................... modelos.py -> calcular_costo()

Registrarse y autenticarse .............................. autenticacion.py

Realizar reservas ....................................... gestores.py

Almacenar reservas en base de datos ..................... base_datos.py + gestores.py

Consultar historial de reservas ......................... GestorReservas.historial()

Validar datos ingresados ................................ validaciones.py

Proteger credenciales y datos sensibles ................. seguridad.py (hash + sal, nunca texto plano)

Consultas SQL seguras ................................... todas usan parámetros (?) -> evita SQL Injection
