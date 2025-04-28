# Sistema Multipropósito: Terminal, Hilos y Sincronización

Sistema cliente-servidor para gestión de archivos remotos con sincronización implementado en Python.

## Objetivos

- Integrar los conceptos de terminal Linux, programación con hilos (threads) y sincronización de procesos.
- Desarrollar una aplicación práctica que combine administración de archivos, comunicación en red y concurrencia.
- Fomentar el trabajo colaborativo mediante roles definidos (cliente-servidor).

## Descripción

Este proyecto implementa un sistema cliente-servidor para la gestión de archivos remotos con sincronización. El sistema permite a los clientes subir, descargar y listar archivos en un servidor remoto, mientras que el servidor procesa solicitudes en paralelo mediante hilos y mantiene la integridad de los datos con mecanismos de sincronización.

## Estructura del Proyecto

```
hilos-sync-system/
├── servidor.py           # Implementación del servidor multihilo
├── cliente.py            # Cliente interactivo para uso del usuario
├── demonio.py            # Proceso demonio para monitoreo del directorio de entrada
├── README.md             # Este archivo
└── docs/                 # Documentación adicional
```

## Requisitos

- Python 3.6 o superior
- Sistema operativo Linux (compatible con Windows con algunas modificaciones)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/AdolfotULS/hilos-sync-system.git
```

2. Navega al directorio del proyecto:
```bash
cd hilos-sync-system
```

3. Prepara el entorno:
```bash
# Crear directorio del servidor si no existe
mkdir -p ~/servidor_archivos/entrada ~/servidor_archivos/procesados ~/servidor_archivos/logs
```

## Uso

### Paso 1: Iniciar el servidor

```bash
python3 servidor.py
```

El servidor iniciará y comenzará a escuchar conexiones de clientes mediante sockets. Procesará múltiples clientes simultáneamente mediante hilos.

### Paso 2: Iniciar el demonio (en una nueva terminal)

```bash
python3 demonio.py
```

El demonio monitoreará el directorio de entrada cada 10 segundos. Cuando detecte nuevos archivos, los procesará y moverá al directorio de procesados.

### Paso 3: Ejecutar el cliente (en una nueva terminal)

```bash
python3 cliente.py
```

El cliente te permitirá:
- Subir un archivo local al servidor
- Descargar un archivo del servidor
- Listar los archivos disponibles en el servidor
- Ver los logs de operaciones

## Componentes Principales

### Servidor Multihilo (servidor.py)

- Escucha conexiones de clientes mediante sockets
- Maneja múltiples clientes simultáneamente con threads
- Proporciona funciones para:
  - Listar archivos en el directorio de entrada
  - Copiar archivos remotos al directorio procesados
  - Leer el contenido de un archivo

### Cliente Interactivo (cliente.py)

- Se conecta al servidor mediante sockets
- Interfaz de usuario que permite:
  - Subir archivos al servidor
  - Descargar archivos del servidor
  - Ver logs de operaciones

### Proceso Demonio (demonio.py)

- Monitorea el directorio de entrada cada 10 segundos
- Inicia un nuevo thread para procesar cada archivo detectado
- Utiliza semáforos (o mutex) para evitar condiciones de carrera
- Mueve los archivos procesados al directorio correspondiente

## Sincronización

El sistema utiliza técnicas de sincronización para evitar condiciones de carrera:

- **Semáforos**: Para controlar el acceso a recursos compartidos
- **Lock**: Para sincronizar el acceso al archivo de registro
- **Algoritmo del Panadero**: Implementado para garantizar la exclusión mutua

## Preguntas Frecuentes

### ¿Cómo evitó condiciones de carrera en el servidor?

Se implementaron semáforos y locks para garantizar que solo un hilo a la vez pueda acceder a los recursos compartidos como el archivo de registro. Esto previene que los hilos interfieran entre sí y causen inconsistencias en los datos.

### ¿Qué ventajas tiene usar threads en lugar de procesos para este caso?

1. **Memoria compartida**: Los threads comparten el espacio de memoria, lo que facilita el intercambio de información.
2. **Menor overhead**: Los threads requieren menos recursos que los procesos completos.
3. **Creación más rápida**: La creación y terminación de threads es más rápida que la de procesos.
4. **Comunicación simplificada**: La comunicación entre threads es más sencilla que entre procesos.

### Explicación del método de sincronización elegido

Se utilizó una combinación de semáforos y locks para la sincronización:

1. **Semáforos**: Controlan el acceso a los directorios compartidos, permitiendo que solo un número limitado de hilos accedan simultáneamente.
2. **Locks**: Garantizan la exclusión mutua al escribir en el archivo de registro, evitando que las entradas se corrompan.

El algoritmo del panadero se implementó para garantizar un acceso justo a los recursos compartidos, evitando la inanición de hilos.

## Ejemplos de Flujo de Trabajo

### Ejemplo 1: Subir y procesar un archivo

1. Cliente1 --> Sube archivo.txt al Servidor
2. Servidor --> Registra en log la operación
3. Demonio --> Detecta el nuevo archivo y lo procesa
4. Demonio --> Mueve archivo.txt a 'procesados'

## Contribución

Este proyecto es parte de una actividad académica. Si deseas contribuir:

1. Realiza un fork del repositorio
2. Crea una nueva rama para tu característica
3. Envía un pull request con tus cambios
