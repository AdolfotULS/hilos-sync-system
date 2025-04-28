import os
import time
import threading
import shutil
import logging
import sys
import platform

# Aca ponemos donde van a estar los archivos (en tu carpeta personal)
BASE_DIR = os.path.expanduser("~/servidor_archivos")

# Estas son las carpetas k vamos a usar
DIR_ENTRADA = os.path.join(BASE_DIR, 'entrada')
DIR_PROCESADOS = os.path.join(BASE_DIR, 'procesados')
DIR_LOGS = os.path.join(BASE_DIR, 'logs')

# Esto crea las carpetas si no existen todavia
for directorio in [DIR_ENTRADA, DIR_PROCESADOS, DIR_LOGS]:
    if not os.path.exists(directorio):
        os.makedirs(directorio)

# Asi guardamos los errores y cosas importantes
logging.basicConfig(
    filename=os.path.join(DIR_LOGS, 'demonio.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Esto es pa k los archivos no se mezclen cuando varios procesos trabajan juntos
archivo_lock = threading.Lock()

# Esta funcion escribe en el log lo k pasa
def registrar_operacion(mensaje):
    with archivo_lock:
        log_path = os.path.join(DIR_LOGS, "registro.log")
        with open(log_path, "a", encoding='utf-8') as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {mensaje}\n")
            logging.info(mensaje)

# Esta funcion mueve los archivo de entrada a prosesados
def procesar_archivo(archivo):
    try:
        origen = os.path.join(DIR_ENTRADA, archivo)
        destino = os.path.join(DIR_PROCESADOS, archivo)
        with archivo_lock:
            # Primero miramos si el archivo todavia existe
            if os.path.exists(origen):
                # Vemos si ya hay un archivo con el mismo nombre
                if os.path.exists(destino):
                    # Si ya existe, le ponemos la fecha al nombre para k sea unico
                    nombre_base, extension = os.path.splitext(archivo)
                    timestamp = time.strftime("%Y%m%d%H%M%S")
                    nuevo_nombre = f"{nombre_base}_{timestamp}{extension}"
                    destino = os.path.join(DIR_PROCESADOS, nuevo_nombre)
                    mensaje = f"El archivo {archivo} ya existe en procesados, renombrando a {nuevo_nombre}"
                    registrar_operacion(mensaje)
                    print(mensaje)
                # Copiamos el archivo y borramos el orijinal
                shutil.copy2(origen, destino)
                os.remove(origen)
                mensaje = f"Archivo {archivo} procesado exitosamente"
                registrar_operacion(mensaje)
                print(mensaje)
            else:
                mensaje = f"El archivo {archivo} ya no existe en la carpeta de entrada"
                registrar_operacion(mensaje)
                logging.warning(mensaje)
                print(mensaje)
    except Exception as e:
        error = f"Error al procesar el archivo {archivo}: {str(e)}"
        registrar_operacion(error)
        logging.error(error)
        print(f"ERROR: {error}")

# Esta es la funcion principal k revisa cada 10 segundos si hay archivos
def monitorear_directorio():
    print(f"Iniciando monitoreo del directorio {DIR_ENTRADA}...")
    registrar_operacion(f"Demonio de monitoreo iniciado en {platform.system()}")
    print(f"Sistema operativo detectado: {platform.system()}")

    # Creamos el log si no existe
    log_path = os.path.join(DIR_LOGS, "registro.log")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding='utf-8') as log_file:
            log_file.write("# Registro de operaciones del servidor de archivos\n")

    # Aqui guardamos los trabajos k estan corriendo
    hilos_activos = []
    
    # Este es el bucle principal k nunca termina
    while True:
        try:
            # Kitamos los trabajos ya terminados
            hilos_activos = [h for h in hilos_activos if h.is_alive()]
            
            # Buscamos archivos nuevos en la carpeta
            archivos = [f for f in os.listdir(DIR_ENTRADA) if os.path.isfile(os.path.join(DIR_ENTRADA, f))]
            
            # Si hay archivos los mostramos
            if archivos:
                mensaje = f"Se encontraron {len(archivos)} archivos para procesar: {', '.join(archivos)}"
                print(mensaje)
                registrar_operacion(mensaje)
            
            # Por cada archivo hacemos un trabajo
            for archivo in archivos:
                thread = threading.Thread(target=procesar_archivo, args=(archivo,))
                thread.start()
                hilos_activos.append(thread)
            
            # Esperamos a k los trabajos terminen
            for hilo in hilos_activos:
                hilo.join(timeout=5)  # esperamos max 5 segundos
            
            # Si no hay nada lo decimos
            if not archivos:
                print("No hay archivos nuevos para procesar. Esperando...")
            
            # Esperamos un ratito antes de revisar otra vez
            time.sleep(10)
            
        except Exception as e:
            error = f"Error durante el monitoreo: {str(e)}"
            registrar_operacion(error)
            logging.error(error)
            print(f"ERROR EN MONITOREO: {error}")
            time.sleep(10)

# Esto es lo k se ejecuta cuando arrancas el programa
if __name__ == "__main__":
    try:
        print(f"Iniciando demonio en {BASE_DIR}")
        print(f"Sistema operativo: {platform.system()}")
        # Empezamos el programa
        monitorear_directorio()
    except KeyboardInterrupt:
        mensaje = "Demonio de monitoreo detenido manualmente"
        registrar_operacion(mensaje)
        print(mensaje)
    except Exception as e:
        error = f"Error fatal en el demonio: {str(e)}"
        registrar_operacion(error)
        logging.critical(error)
        print(f"ERROR FATAL: {error}")