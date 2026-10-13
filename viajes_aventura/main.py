"""
main.py
Punto de entrada del sistema Viajes Aventura. Ejecutar con:  python main.py
"""
import autenticacion
import base_datos
import menus


def main():
    base_datos.crear_tablas()          # crea la base de datos si no existe
    autenticacion.crear_admin_inicial()  # pide crear el admin la primera vez
    menus.menu_principal()


if __name__ == "__main__":
    main()
