import socket
import os
from pathlib import Path
import ipaddress

class ClienteArchivos:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.socket = None
        self.buffer_size = 4096

    def conectar(self):
        """Establece conexion con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Conectado al servidor {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def cerrar(self):
        """Cierra la conexion con el servidor"""
        if self.socket:
            self.socket.close()
            print("Conexion cerrada")

    def enviar_comando(self, comando):
        """Envia un comando al servidor y recibe la respuesta"""
        try:
            self.socket.sendall(comando.encode('utf-8'))
            respuesta = self.socket.recv(self.buffer_size).decode('utf-8')
            return respuesta
        except Exception as e:
            print(f"Error en la comunicacion: {e}")
            return None

    def listar_archivos(self):
        """Lista los archivos disponibles en el servidor"""
        respuesta = self.enviar_comando("LISTAR|")
        print("\nArchivos en el servidor:")
        print(respuesta)

    def leer_archivo(self, nombre_archivo):
        """Lee el contenido de un archivo del servidor"""
        comando = f"LEER|{nombre_archivo}"
        respuesta = self.enviar_comando(comando)
        print(f"\nContenido del archivo {nombre_archivo}:")
        print(respuesta)

    def subir_archivo(self, ruta_archivo):
        """Sube un archivo al servidor"""
        if not os.path.exists(ruta_archivo):
            print(f"Error: El archivo {ruta_archivo} no existe")
            return

        try:
            with open(ruta_archivo, 'r') as f:
                contenido = f.read()
                nombre_archivo = os.path.basename(ruta_archivo)
                comando = f"SUBIR|{nombre_archivo}|{contenido}"
                respuesta = self.enviar_comando(comando)
                print(respuesta)
        except Exception as e:
            print(f"Error al subir el archivo: {e}")

    def descargar_archivo(self, nombre_archivo):
        """Descarga un archivo del servidor"""
        comando = f"DESCARGAR|{nombre_archivo}"
        respuesta = self.enviar_comando(comando)

        if "Error" in respuesta:
            print(respuesta)
            return

        try:
            with open(nombre_archivo, 'w') as f:
                f.write(respuesta)
            print(f"Archivo {nombre_archivo} descargado exitosamente")
        except Exception as e:
            print(f"Error al guardar el archivo descargado: {e}")

    def ver_logs(self):
        """Solicita y muestra los logs del servidor"""
        respuesta = self.enviar_comando("LOGS|")
        print("\nRegistro de operaciones del servidor:")
        print(respuesta)

def preguntar_host():
    while True:
        h = input("IP del servidor (o 'localhost'): ")
        if h.lower() == 'localhost':
            return '127.0.0.1'
        try:
            ipaddress.ip_address(h)
            return h
        except ValueError:
            print("-> IP invalida, intente de nuevo.")

def preguntar_port():
    while True:
        try:
            p = int(input("Puerto (1–65535): "))
            if 1 <= p <= 65535:
                return p
        except ValueError:
            pass
        print("-> Puerto invalido, ingrese un numero entre 1 y 65535.")

def mostrar_menu():
    """Muestra el menu de opciones disponibles"""
    print("\n=== CLIENTE DE ARCHIVOS ===")
    print("1. Listar archivos")
    print("2. Leer archivo")
    print("3. Subir archivo")
    print("4. Descargar archivo")
    print("5. Ver logs")
    print("0. Salir")
    return input("Seleccione una opcion: ")

def main():
    """Funcion principal del cliente"""
    host = preguntar_host()
    port = preguntar_port()

    cliente = ClienteArchivos(host, port)
    if not cliente.conectar():
        return

    try:
        while True:
            opcion = mostrar_menu()

            if opcion == "1":
                cliente.listar_archivos()

            elif opcion == "2":
                nombre_archivo = input("Ingrese el nombre del archivo a leer: ")
                cliente.leer_archivo(nombre_archivo)

            elif opcion == "3":
                ruta_archivo = input("Ingrese la ruta del archivo a subir: ")
                cliente.subir_archivo(ruta_archivo)

            elif opcion == "4":
                nombre_archivo = input("Ingrese el nombre del archivo a descargar: ")
                cliente.descargar_archivo(nombre_archivo)

            elif opcion == "5":
                cliente.ver_logs()

            elif opcion == "0":
                break

            else:
                print("Opcion no valida")

    except KeyboardInterrupt:
        print("\nOperacion interrumpida por el usuario")
    finally:
        cliente.cerrar()

if __name__ == "__main__":
    main()
