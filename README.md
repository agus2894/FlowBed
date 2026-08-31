# 🏥 FlowBed

**Sistema inteligente de gestión de flujo de pacientes en guardia hospitalaria**

FlowBed es una aplicación web que optimiza la gestión de posiciones asistenciales en tiempo real, permitiendo identificar cuellos de botella y mejorar los tiempos de espera para asignación de camas.

## 🎯 Características

- **22 posiciones asistenciales**:
  - 9 camas (C1–C9)
  - 8 consultorios (CONS1–CONS8)
  - 4 shock rooms (SR1–SR4)
  - 1 aislamiento (ISO1)

- **Estados de posiciones**:
  - ✅ LIBRE
  - 🔴 OCUPADO
  - 🧹 LIMPIEZA
  - 🔵 RESERVADO
  - ⚠️ FUERA_SERVICIO

- **Funcionalidades**:
  - Dashboard en tiempo real con todas las posiciones
  - Cambio de estado con un click
  - **Selección de destino al ocupar**: Al cargar un paciente, se debe seleccionar su destino (PISO, UTI, UTIM)
  - **Cronómetro en tiempo real**: Muestra el tiempo transcurrido desde que se ocupó la posición
  - **Marcar destino asignado**: Detiene el cronómetro cuando el paciente obtiene su cama final
  - **Historial completo**: Registro de todos los pacientes con tiempos de espera
  - **Análisis de cuellos de botella**: Estadísticas por destino para identificar demoras
  - **Alertas visuales**: Tiempos coloreados según criticidad (verde < 30min, amarillo < 60min, rojo > 60min)

## 🚀 Inicio Rápido (Instalación y Ejecución)

Sigue estos sencillos pasos para poner en marcha el proyecto en tu máquina local:

### 1. Ubicarse en el directorio del proyecto
```bash
cd /ruta/hacia/Gestor_Camas
```

### 2. Activar el entorno virtual

- **En Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```
- **En Windows (PowerShell / CMD)**:
  ```cmd
  venv\Scripts\activate
  ```
  *(Nota: Si necesitas crear un entorno virtual nuevo desde cero, ejecuta `python -m venv venv` antes de activarlo).*

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Aplicar las migraciones de la base de datos
```bash
python manage.py migrate
```

### 5. Inicializar las posiciones asistenciales *(Solo la primera vez)*
Crea automáticamente las 22 posiciones (9 camas, 8 consultorios, 4 shock rooms y 1 aislamiento):
```bash
python manage.py inicializar_posiciones
```

### 6. Iniciar el servidor
```bash
python manage.py runserver
```

### 7. Abrir la aplicación
Accede desde tu navegador web a:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

### 🧪 Ejecutar los Tests Automatizados
Para verificar que todos los módulos y endpoints funcionen correctamente:
```bash
python manage.py test
```

---

## 📱 Manual de Uso Rápido

### Ocupar una posición con paciente
1. Hacer click en una posición LIBRE
2. Seleccionar estado "Ocupado"
3. Ingresar el nombre del paciente
4. **Seleccionar el destino del paciente** (PISO, UTI o UTIM)
5. Click en "Guardar"
6. La posición mostrará:
   - Nombre del paciente
   - Destino solicitado
   - **Cronómetro en tiempo real** que cuenta el tiempo de espera

### Marcar destino asignado (detener cronómetro)
1. Cuando el paciente obtenga su cama final, click en **"📍 Marcar Destino"**
2. Seleccionar el destino final donde fue asignado
3. El cronómetro **se detiene automáticamente** ⏹️
4. Se registra el evento en el historial con el tiempo exacto de espera

### Ver historial y estadísticas
1. Click en **"📊 Ver Historial y Estadísticas"** en el dashboard
2. Analiza:
   - Tiempos promedio por destino (identifica cuellos de botella)
   - Historial completo de pacientes con tiempos de espera
   - Estadísticas generales del sistema

### Desocupar una posición
1. Cambiar una posición OCUPADA a otro estado (LIBRE, LIMPIEZA, etc.)
2. El sistema limpia todos los datos automáticamente


## 🎨 Tecnologías

- **Backend**: Django (Python)
- **Frontend**: HTML5 + CSS3 moderno + JavaScript Vanilla (Modular en `guardia/static/`)
- **Visualización Analítica**: Chart.js
- **Tiempo Real**: Server-Sent Events (SSE) con `EventSource` y reconexión automática
- **Base de datos**: SQLite

## 📝 Notas

- La aplicación se actualiza en tiempo real instantáneo mediante Server-Sent Events (SSE)
- No requiere autenticación (diseñado para estaciones y terminales compartidas de guardia)
- Notificaciones flotantes tipo Toast para alertar cambios entre operadores
- Buscador y filtrado dinámico en tiempo real
- Gráficos interactivos de tiempos de espera y cuellos de botella por destino

## 📈 Próximas mejoras (opcional)

- Exportar reportes en PDF/Excel
- Integración con sistema de historias clínicas (HL7 / FHIR)
- Sistema de Triage por criticidad
- Autenticación y roles de usuario (opcional)

---

**Autor**: Lamas Gonzalo  
**Versión**: 2.0  
**Fecha**: 2026

# FlowBed