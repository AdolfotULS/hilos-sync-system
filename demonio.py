import os 
import time
import threading
import shutil
import logging

# configuracion de logging
logging.basicConfig(
    filename='servidor_archivos/logs/demonio.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# carpetas del sistema
DIR_ENTRADA = 'servidor_archivos/entrada'
DIR_PROCESADOS = 'servidor_archivos/procesados'
DIR_LOGS = 'servidor_archivos/logs'

# candado para evitar problemas
archivo_lock = threading.Lock()

# funcion para guardar lo que hace el programa
def registrar_operacion(mensaje):
    with archivo_lock:
        with open(f"{DIR_LOGS}/registro.log", "a") as log_file:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] {mensaje}\n")
            logging.info(mensaje)
            
# funcion para mover archivos de entrada a procesados
def procesar_archivo(archivo):
    try:
        origen = os.path.join(DIR_ENTRADA, archivo)
        destino = os.path.join(DIR_PROCESADOS, archivo)
        
        with archivo_lock:
            # verifico si todavia existe
            if os.path.exists(origen):
                # copio y luego borro el original
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

# funcion principal que revisa cada 10 segundos
def monitorear_directorio():
    print(f"Iniciando monitoreo del directorio {DIR_ENTRADA}...")
    registrar_operacion("Demonio de monitoreo iniciado")

    # creo el archivo de log si no existe
    if not os.path.exists(f"{DIR_LOGS}/registro.log"):
        with open(f"{DIR_LOGS}/registro.log", "w") as log_file:
            log_file.write("# Registro de operaciones del servidor de archivos\n")
    
    while True:
        try:
            # busco archivos nuevos
            archivos = [f for f in os.listdir(DIR_ENTRADA) if os.path.isfile(os.path.join(DIR_ENTRADA, f))]
            
            # proceso cada archivo con un hilo separado
            for archivo in archivos:
                thread = threading.Thread(target=procesar_archivo, args=(archivo,))
                thread.start()

            # espero 10 segundos antes de revisar de nuevo
            time.sleep(10)
        except Exception as e:
            error = f"Error durante el monitoreo: {str(e)}"
            registrar_operacion(error)
            logging.error(error)
            time.sleep(10)

if __name__ == "__main__":
    try:
        # creo los directorios si no existen
        for directorio in [DIR_ENTRADA, DIR_PROCESADOS, DIR_LOGS]:
            if not os.path.exists(directorio):
                os.makedirs(directorio)
                registrar_operacion(f"Directorio {directorio} creado")

        # inicio el monitoreo
        monitorear_directorio()
    except KeyboardInterrupt:
        registrar_operacion("Demonio de monitoreo detenido manualmente")
        print("Monitoreo detenido manualmente")
    except Exception as e:
        error = f"Error fatal en el demonio: {str(e)}"
        registrar_operacion(error)
        logging.critical(error)