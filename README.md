# 🏥 Sistema de Gestión de Guardia Hospitalaria

Aplicación web simple para gestionar el flujo de pacientes en una Guardia hospitalaria.

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
  - Registro automático de egreso con duración cuando el paciente se desocupa
  - Historial de egresos con timestamp y duración de estadía

## 🚀 Instalación y Uso

### 1. Activar el entorno virtual (si es necesario)
```bash
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate  # En Windows
```

### 2. Instalar dependencias (si es la primera vez)
```bash
pip install django
```

### 3. Inicializar las posiciones (solo la primera vez)
```bash
python3 manage.py inicializar_posiciones
```

### 4. Iniciar el servidor
```bash
python3 manage.py runserver
```

### 5. Abrir el navegador
Ir a: **http://127.0.0.1:8000/**

## 📱 Cómo usar la aplicación

### Ocupar una posición con paciente
1. Hacer click en una posición LIBRE
2. Seleccionar estado "Ocupado"
3. Ingresar el nombre del paciente
4. **Seleccionar el destino del paciente** (PISO, UTI o UTIM)
5. Click en "Guardar"
6. La posición mostrará:
   - Nombre del paciente
   - Destino seleccionado
   - **Cronómetro en tiempo real** que cuenta el tiempo desde que se ocupó

### Desocupar una posición
1. Cambiar una posición OCUPADA a cualquier otro estado (LIBRE, LIMPIEZA, etc.)
2. El sistema automáticamente:
   - Registra un EventoEgreso con el destino previamente seleccionado
   - Calcula la duración de estadía
   - Guarda timestamp de ingreso y egreso
   - Limpia la posición

### Cambiar otros estados
1. Hacer click en cualquier posición
2. Seleccionar el nuevo estado (RESERVADO, FUERA_SERVICIO, etc.)
3. Click en "Guardar"

## 🗂️ Estructura del proyecto

```
Gestor_Camas/
├── manage.py
├── Gestores/
│   ├── settings.py      # Configuración de Django
│   ├── urls.py          # URLs principales
│   └── ...
└── guardia/
    ├── models.py        # Modelos: Posicion, EventoEgreso
    ├── views.py         # Vistas y APIs
    ├── urls.py          # URLs de la app
    ├── admin.py         # Configuración del admin
    ├── templates/
    │   └── guardia/
    │       └── dashboard.html  # Template principal
    └── management/
        └── commands/
            └── inicializar_posiciones.py
```

## 📊 Modelos de Base de Datos
- `timestamp_ingreso` (DateTimeField): Timestamp de cuándo se ocupó la posición
- `destino_solicitado` (CharField): Destino del paciente (PISO, UTI, UTIM)

### Posicion
- `id` (CharField): ID único (ej: "C1", "CONS1", "SR1", "ISO1")
- `tipo` (CharField): cama, consultorio, shock, aislamiento
- `estado` (CharField): LIBRE, OCUPADO, LIMPIEZA, RESERVADO, FUERA_SERVICIO
- `timestamp_estado` (DateTimeField): Timestamp del último cambio de estado
- `nombre_paciente` (CharField): Nombre del paciente (opcional)

### EventoEgreso
- `posicion_id` (CharField): ID de la posición
- `paciente` (CharField): Nombre del paciente
- `destino` (CharField): PISO, UTI, UTIM
- `timestamp_ingreso` (DateTimeField): Cuándo ingresó el paciente
- `timestamp_egreso` (DateTimeField): Cuándo egresó el paciente
- `duracion` (DurationField): Duración calculada automáticamente

## 🔧 Administración

Para acceder al panel de administración de Django:

1. Crear un superusuario:
```bash
python3 manage.py createsuperuser
```

2. Ir a: **http://127.0.0.1:8000/admin/**

3. Desde allí puedes ver:
   - Todas las posiciones
   - Historial de egresos
   - Estadísticas y filtros

## 🎨 Tecnologías

- **Backend**: Django 6.0.7
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Base de datos**: SQLite
- **Sin frameworks JS**: Todo el código JS está embebido en el template

## 📝 Notas

- La aplicación actualiza automáticamente cada 30 segundos
- No requiere autenticación (según especificaciones)
- Ideal para uso en hospitales con pantallas compartidas
- Código comentado y simple para fácil mantenimiento

## 🛠️ Comandos útiles

```bash
# Crear migraciones (si modificas modelos)
python3 manage.py makemigrations

# Aplicar migraciones
python3 manage.py migrate

# Reinicializar todas las posiciones
python3 manage.py inicializar_posiciones

# Ver historial de egresos en la terminal
python3 manage.py shell
>>> from guardia.models import EventoEgreso
>>> for e in EventoEgreso.objects.all():
...     print(f"{e.paciente} - {e.posicion_id} → {e.destino} ({e.duracion})")
```

## 📈 Próximas mejoras (opcional)

- Agregar gráficos de estadísticas
- Exportar reportes en PDF/Excel
- Notificaciones por email/SMS
- Integración con sistema de historias clínicas
- Autenticación y roles de usuario
- Vista de histórico completo en el dashboard

---

**Autor**: Sistema de Gestión Hospitalaria  
**Versión**: 1.0  
**Fecha**: 2026
