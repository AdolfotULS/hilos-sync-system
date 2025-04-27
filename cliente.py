import socket
import threading
import os
import logging
import time
from pathlib import Path
from threading import Lock

class ServidorArchivos:
    def __init__(self, host='localhost', port=5000):
        # Configuración básica
        self.host = host
        self.port = port

        # Directorios del sistema
        self.base_dir = Path(os.path.expanduser('~/servidor_archivos'))
        self.entrada_dir = self.base_dir / 'entrada'
        self.procesados_dir = self.base_dir / 'procesados'
        self.logs_dir = self.base_dir / 'logs'

        # Crear directorios si no existen
        self._crear_estructura_directorios()

        # Configuración de logging
        self._configurar_logging()

        # Locks para sincronización
        self.log_lock = Lock()
        self.file_lock = Lock()

    def _crear_estructura_directorios(self):
        """Crea la estructura de directorios necesaria"""
        for directorio in [self.entrada_dir, self.procesados_dir, self.logs_dir]:
            directorio.mkdir(parents=True, exist_ok=True)

    def _configurar_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            filename=self.logs_dir / 'registro.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    def registrar_operacion(self, mensaje):
        """Registra operaciones de forma thread-safe"""
        with self.log_lock:
            logging.info(mensaje)

    def listar_archivos_entrada(self):
        """Lista los archivos en el directorio de entrada"""
        try:
            archivos = [f.name for f in self.entrada_dir.glob('*') if f.is_file()]
            return '\n'.join(archivos) if archivos else "No hay archivos"
        except Exception as e:
            self.registrar_operacion(f"Error al listar archivos: {str(e)}")
            return "Error al listar archivos"

    def leer_archivo(self, nombre_archivo):
        """Lee el contenido de un archivo de forma segura"""
        ruta_archivo = self.entrada_dir / nombre_archivo
        try:
            with self.file_lock:
                if not ruta_archivo.exists():
                    return "El archivo no existe"
                with open(ruta_archivo, 'r') as f:
                    contenido = f.read()
                self.registrar_operacion(f"Archivo leído: {nombre_archivo}")
                return contenido
        except Exception as e:
            self.registrar_operacion(f"Error al leer archivo {nombre_archivo}: {str(e)}")
            return f"Error al leer archivo: {str(e)}"

    def copiar_a_procesados(self, nombre_archivo):
        """Copia un archivo al directorio de procesados"""
        archivo_origen = self.entrada_dir / nombre_archivo
        archivo_destino = self.procesados_dir / nombre_archivo

        try:
            with self.file_lock:
                if not archivo_origen.exists():
                    return "El archivo no existe"

                with open(archivo_origen, 'rb') as f_origen:
                    contenido = f_origen.read()

                with open(archivo_destino, 'wb') as f_destino:
                    f_destino.write(contenido)

                self.registrar_operacion(f"Archivo copiado a procesados: {nombre_archivo}")
                return "Archivo copiado exitosamente"
        except Exception as e:
            self.registrar_operacion(f"Error al copiar archivo {nombre_archivo}: {str(e)}")
            return f"Error al copiar archivo: {str(e)}"

    def manejar_cliente(self, conn, addr):
        """Maneja las conexiones de los clientes"""
        self.registrar_operacion(f"Nueva conexión desde {addr}")

        try:
            while True:
                comando = conn.recv(1024).decode()
                if not comando:
                    break

                partes = comando.split()
                if not partes:
                    continue

                accion = partes[0].upper()

                if accion == "LISTAR":
                    respuesta = self.listar_archivos_entrada()
                elif accion == "LEER" and len(partes) > 1:
                    respuesta = self.leer_archivo(partes[1])
                elif accion == "COPIAR" and len(partes) > 1:
                    respuesta = self.copiar_a_procesados(partes[1])
                else:
                    respuesta = "Comando no válido"

                conn.send(respuesta.encode())

        except Exception as e:
            self.registrar_operacion(f"Error en conexión con {addr}: {str(e)}")
        finally:
            conn.close()
            self.registrar_operacion(f"Conexión cerrada con {addr}")

    def iniciar(self):
        """Inicia el servidor"""
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind((self.host, self.port))
        servidor.listen(5)

        self.registrar_operacion("Servidor iniciado")
        print(f"Servidor escuchando en {self.host}:{self.port}")

        try:
            while True:
                conn, addr = servidor.accept()
                thread_cliente = threading.Thread(
                    target=self.manejar_cliente,
                    args=(conn, addr)
                )
                thread_cliente.start()
        except KeyboardInterrupt:
            self.registrar_operacion("Servidor detenido")
            servidor.close()

if __name__ == "__main__":
    servidor = ServidorArchivos()
    servidor.iniciar()