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

## 📱 Cómo usar la aplicación

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

- **Backend**: Django 6.0.7
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Base de datos**: SQLite
- **Sin frameworks JS**: Todo el código JS está embebido en el template

## 📝 Notas

- La aplicación actualiza automáticamente cada 30 segundos
- No requiere autenticación (según especificaciones)
- Ideal para uso en hospitales con pantallas compartidas
- Código comentado y simple para fácil mantenimiento


## 📈 Próximas mejoras (opcional)

- Agregar gráficos de estadísticas
- Exportar reportes en PDF/Excel
- Notificaciones por email/SMS
- Integración con sistema de historias clínicas
- Autenticación y roles de usuario
- Vista de histórico completo en el dashboard

---

**Autor**: Lamas Gonzalo  
**Versión**: 1.0  
**Fecha**: 2026

# FlowBed