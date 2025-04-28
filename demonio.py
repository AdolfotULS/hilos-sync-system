import os
import time
import threading
import shutil
import logging
import sys
import platform

# Veo que sistema operativo es y pongo la carpeta donde corresponde
if platform.system() == "Windows":
    # En Windows uso la carpeta Documentos
    BASE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "servidor_archivos")
else:
    # En Linux o Mac uso la carpeta del usuario
    BASE_DIR = os.path.expanduser("~/servidor_archivos")

# Creo nombres para las carpetas que voy a usar
DIR_ENTRADA = os.path.join(BASE_DIR, 'entrada')
DIR_PROCESADOS = os.path.join(BASE_DIR, 'procesados')
DIR_LOGS = os.path.join(BASE_DIR, 'logs')

# Me aseguro que existan las carpetas
for directorio in [DIR_ENTRADA, DIR_PROCESADOS, DIR_LOGS]:
    if not os.path.exists(directorio):
        os.makedirs(directorio)

# Configuro el log para guardar errores
logging.basicConfig(
    filename=os.path.join(DIR_LOGS, 'demonio.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Esto es para que no se mezclen los archivos
archivo_lock = threading.Lock()

# Esta funcion guarda mensajes en el log
def registrar_operacion(mensaje):
    with archivo_lock:
        log_path = os.path.join(DIR_LOGS, "registro.log")
        with open(log_path, "a", encoding='utf-8') as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {mensaje}\n")
            logging.info(mensaje)
# Esta funcion copia archivos de entrada a procesados
def procesar_archivo(archivo):
    try:
        origen = os.path.join(DIR_ENTRADA, archivo)
        destino = os.path.join(DIR_PROCESADOS, archivo)
        with archivo_lock:
            # Primero veo si el archivo sigue ahi
            if os.path.exists(origen):
                # Veo si ya hay uno igual en procesados
                if os.path.exists(destino):
                    # Si ya hay uno igual, le pongo la fecha y hora al nombre
                    nombre_base, extension = os.path.splitext(archivo)
                    timestamp = time.strftime("%Y%m%d%H%M%S")
                    nuevo_nombre = f"{nombre_base}_{timestamp}{extension}"
                    destino = os.path.join(DIR_PROCESADOS, nuevo_nombre)
                    mensaje = f"El archivo {archivo} ya existe en procesados, renombrando a {nuevo_nombre}"
                    registrar_operacion(mensaje)
                    print(mensaje)
                # Copio el archivo y borro el original
                shutil.copy2(origen, destino)
                os.remove(origen)
                mensaje = f"Archivo {archivo} procesado exitosamente"
                registrar_operacion(mensaje)
                print(mensaje)
            else:
                logging.warning(f"El archivo {archivo} ya no existe en la carpeta de entrada")
    except Exception as e:
        error = f"Error al procesar el archivo {archivo}: {str(e)}"
        registrar_operacion(error)
        logging.error(error)

# Esta es la funcion principal que revisa cada 10 segundos si hay archivos nuevos
def monitorear_directorio():
    print(f"Iniciando monitoreo del directorio {DIR_ENTRADA}...")
    registrar_operacion(f"Demonio de monitoreo iniciado en {platform.system()}")
    print(f"Sistema operativo detectado: {platform.system()}")

    # Creo el archivo de registro si no existe
    log_path = os.path.join(DIR_LOGS, "registro.log")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding='utf-8') as log_file:
            log_file.write("# Registro de operaciones del servidor de archivos\n")
    while True:
        try:
            # Busco los archivos que hay en la carpeta entrada
            archivos = [f for f in os.listdir(DIR_ENTRADA) if os.path.isfile(os.path.join(DIR_ENTRADA, f))]
            # Por cada archivo creo un hilo para que trabaje rapido
            for archivo in archivos:
                thread = threading.Thread(target=procesar_archivo, args=(archivo,))
                thread.start()

            # Espero 10 segundos para no estar revisando todo el tiempo
            time.sleep(10)
        except Exception as e:
            error = f"Error durante el monitoreo: {str(e)}"
            registrar_operacion(error)
            logging.error(error)
            time.sleep(10)

if __name__ == "__main__":
    try:
        print(f"Iniciando demonio en {BASE_DIR}")
        print(f"Sistema operativo: {platform.system()}")
        # Inicio el programa principal
        monitorear_directorio()
    except KeyboardInterrupt:
        registrar_operacion("Demonio de monitoreo detenido manualmente")
        print("Monitoreo detenido manualmente")
    except Exception as e:
        error = f"Error fatal en el demonio: {str(e)}"
        registrar_operacion(error)
        logging.critical(error)