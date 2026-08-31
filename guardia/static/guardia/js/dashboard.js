/**
 * FlowBed - Real-Time Dashboard Client
 * Server-Sent Events (SSE), Live Stopwatch, KPI Counters, Search & Filters
 */

let posiciones = [];
let posicionesPreviasMap = new Map();
let posicionSeleccionada = null;
let posicionDestinoId = null;
let filtroActual = 'TODOS';
let terminoBusqueda = '';
let eventSource = null;

// ==========================================================================
// 1. Inicialización y Conexión en Tiempo Real (SSE)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    inicializarEventSource();
    inicializarControles();
    setInterval(actualizarCronometros, 1000);
});

function inicializarEventSource() {
    const syncDot = document.getElementById('sync-dot');
    const syncText = document.getElementById('sync-text');

    if (window.EventSource) {
        eventSource = new EventSource('/api/posiciones/stream/');

        eventSource.addEventListener('init', (e) => {
            const data = JSON.parse(e.data);
            posiciones = data.posiciones;
            actualizarMapaPrevio(posiciones);
            actualizarKPIs();
            renderizarPosiciones();
            setSyncStatus(true);
        });

        eventSource.addEventListener('update', (e) => {
            const data = JSON.parse(e.data);
            detectarCambiosYNotificar(data.posiciones);
            posiciones = data.posiciones;
            actualizarMapaPrevio(posiciones);
            actualizarKPIs();
            renderizarPosiciones();
            setSyncStatus(true);
        });

        eventSource.onerror = () => {
            setSyncStatus(false);
            // Fallback a polling si se interrumpe la conexión
            setTimeout(cargarPosicionesFallback, 5000);
        };
    } else {
        // Fallback para navegadores antiguos
        cargarPosicionesFallback();
        setInterval(cargarPosicionesFallback, 5000);
    }
}

function setSyncStatus(isOnline) {
    const syncDot = document.getElementById('sync-dot');
    const syncText = document.getElementById('sync-text');
    if (!syncDot || !syncText) return;

    if (isOnline) {
        syncDot.classList.remove('offline');
        syncText.textContent = 'En vivo';
    } else {
        syncDot.classList.add('offline');
        syncText.textContent = 'Reconectando...';
    }
}

async function cargarPosicionesFallback() {
    try {
        const response = await fetch('/api/posiciones/');
        const data = await response.json();
        detectarCambiosYNotificar(data.posiciones);
        posiciones = data.posiciones;
        actualizarMapaPrevio(posiciones);
        actualizarKPIs();
        renderizarPosiciones();
        setSyncStatus(true);
    } catch (error) {
        console.error('Error al cargar posiciones:', error);
        setSyncStatus(false);
    }
}

function actualizarMapaPrevio(lista) {
    posicionesPreviasMap.clear();
    lista.forEach(p => posicionesPreviasMap.set(p.id, { ...p }));
}

function detectarCambiosYNotificar(nuevasPosiciones) {
    if (posicionesPreviasMap.size === 0) return;

    nuevasPosiciones.forEach(nueva => {
        const previa = posicionesPreviasMap.get(nueva.id);
        if (!previa) return;

        if (previa.estado !== nueva.estado) {
            if (nueva.estado === 'OCUPADO') {
                mostrarToast(`🔴 <strong>${nueva.id}</strong> ocupada por ${nueva.nombre_paciente || 'paciente'}`, 'danger');
            } else if (nueva.estado === 'LIBRE') {
                mostrarToast(`🟢 <strong>${nueva.id}</strong> ahora está LIBRE`, 'success');
            } else if (nueva.estado === 'LIMPIEZA') {
                mostrarToast(`🧹 <strong>${nueva.id}</strong> en limpieza`, 'warning');
            } else {
                mostrarToast(`ℹ️ <strong>${nueva.id}</strong> cambió a ${nueva.estado}`, 'info');
            }
        } else if (!previa.destino_asignado && nueva.destino_asignado) {
            mostrarToast(`📍 <strong>${nueva.id}</strong> asignada a ${nueva.destino_asignado}`, 'success');
        }
    });
}

// ==========================================================================
// 2. KPIs y Contadores
// ==========================================================================

function actualizarKPIs() {
    const total = posiciones.length;
    const ocupadas = posiciones.filter(p => p.estado === 'OCUPADO').length;
    const libres = posiciones.filter(p => p.estado === 'LIBRE').length;
    const limpieza = posiciones.filter(p => p.estado === 'LIMPIEZA').length;
    const shockOcupados = posiciones.filter(p => p.tipo === 'shock' && p.estado === 'OCUPADO').length;
    
    const porcentajeOcupacion = total > 0 ? Math.round((ocupadas / total) * 100) : 0;

    const elTotal = document.getElementById('kpi-total');
    const elOcupadas = document.getElementById('kpi-ocupadas');
    const elLibres = document.getElementById('kpi-libres');
    const elLimpieza = document.getElementById('kpi-limpieza');
    const elShock = document.getElementById('kpi-shock');
    const elPorcentaje = document.getElementById('kpi-porcentaje');

    if (elTotal) elTotal.textContent = total;
    if (elOcupadas) elOcupadas.textContent = ocupadas;
    if (elLibres) elLibres.textContent = libres;
    if (elLimpieza) elLimpieza.textContent = limpieza;
    if (elShock) elShock.textContent = shockOcupados;
    if (elPorcentaje) elPorcentaje.textContent = `${porcentajeOcupacion}%`;
}

// ==========================================================================
// 3. Renderizado y Filtros
// ==========================================================================

function inicializarControles() {
    const inputBuscar = document.getElementById('input-busqueda');
    if (inputBuscar) {
        inputBuscar.addEventListener('input', (e) => {
            terminoBusqueda = e.target.value.toLowerCase().trim();
            renderizarPosiciones();
        });
    }

    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filtroActual = btn.dataset.filtro;
            renderizarPosiciones();
        });
    });
}

function cumpleFiltro(pos) {
    // Filtro por texto (id o nombre paciente)
    if (terminoBusqueda) {
        const idMatch = pos.id.toLowerCase().includes(terminoBusqueda);
        const pacienteMatch = pos.nombre_paciente ? pos.nombre_paciente.toLowerCase().includes(terminoBusqueda) : false;
        if (!idMatch && !pacienteMatch) return false;
    }

    // Filtro por pestaña
    if (filtroActual === 'TODOS') return true;
    if (filtroActual === 'OCUPADO') return pos.estado === 'OCUPADO';
    if (filtroActual === 'LIBRE') return pos.estado === 'LIBRE';
    if (filtroActual === 'LIMPIEZA') return pos.estado === 'LIMPIEZA';
    if (filtroActual === 'cama') return pos.tipo === 'cama';
    if (filtroActual === 'consultorio') return pos.tipo === 'consultorio';
    if (filtroActual === 'shock') return pos.tipo === 'shock';
    if (filtroActual === 'aislamiento') return pos.tipo === 'aislamiento';

    return true;
}

function renderizarPosiciones() {
    const grillas = {
        'cama': document.getElementById('grilla-camas'),
        'consultorio': document.getElementById('grilla-consultorios'),
        'shock': document.getElementById('grilla-shock'),
        'aislamiento': document.getElementById('grilla-aislamiento'),
    };

    const badges = {
        'cama': document.getElementById('badge-camas'),
        'consultorio': document.getElementById('badge-consultorios'),
        'shock': document.getElementById('badge-shock'),
        'aislamiento': document.getElementById('badge-aislamiento'),
    };

    // Limpiar grillas
    Object.values(grillas).forEach(g => { if (g) g.innerHTML = ''; });

    // Contadores por tipo visibles
    const conteos = { 'cama': 0, 'consultorio': 0, 'shock': 0, 'aislamiento': 0 };

    posiciones.forEach(pos => {
        if (cumpleFiltro(pos)) {
            const elem = crearElementoPosicion(pos);
            if (grillas[pos.tipo]) {
                grillas[pos.tipo].appendChild(elem);
                conteos[pos.tipo]++;
            }
        }
    });

    // Actualizar badges con cantidad visible
    Object.keys(badges).forEach(tipo => {
        if (badges[tipo]) badges[tipo].textContent = conteos[tipo];
    });

    // Ocultar sección si no tiene items tras filtrar
    Object.keys(grillas).forEach(tipo => {
        const sec = document.getElementById(`seccion-${tipo}`);
        if (sec) {
            sec.style.display = conteos[tipo] === 0 && (filtroActual !== 'TODOS' || terminoBusqueda) ? 'none' : 'block';
        }
    });

    actualizarCronometros();
}

function crearElementoPosicion(pos) {
    const card = document.createElement('div');
    card.className = `posicion-card ${pos.estado}`;
    card.dataset.posicionId = pos.id;
    card.onclick = () => abrirModal(pos);

    const estadoTexto = {
        'LIBRE': 'Libre',
        'OCUPADO': 'Ocupado',
        'LIMPIEZA': 'En Limpieza',
        'RESERVADO': 'Reservado',
        'FUERA_SERVICIO': 'F. Servicio'
    };

    const destinoIconos = {
        'PISO': '🏥 Piso',
        'UTI': '🚨 UTI',
        'UTIM': '⚕️ UTIM'
    };

    let html = `
        <div class="posicion-top">
            <div class="posicion-id">${pos.id}</div>
            <div class="posicion-estado-badge">${estadoTexto[pos.estado] || pos.estado}</div>
        </div>
        <div class="posicion-body">
    `;

    if (pos.nombre_paciente) {
        html += `<div class="posicion-paciente" title="${pos.nombre_paciente}">👤 ${pos.nombre_paciente}</div>`;
    }

    if (pos.destino_solicitado) {
        html += `<div class="posicion-destino-solicitado"><span>Destino:</span> ${destinoIconos[pos.destino_solicitado] || pos.destino_solicitado}</div>`;
    }

    if (pos.destino_asignado) {
        html += `<div class="posicion-destino-asignado">✅ Asignado a ${pos.destino_asignado}</div>`;
    }

    if (pos.estado === 'OCUPADO' && pos.timestamp_ingreso) {
        const timestampFin = pos.timestamp_destino_asignado || null;
        html += `<div class="posicion-cronometro crono-normal" data-timestamp="${pos.timestamp_ingreso}" data-timestamp-fin="${timestampFin || ''}">⏱️ 00:00:00</div>`;
    }

    html += `</div>`;

    if (pos.estado === 'OCUPADO' && !pos.destino_asignado) {
        html += `
            <button class="btn-marcar-destino" onclick="event.stopPropagation(); abrirModalDestino('${pos.id}')">
                📍 Marcar Destino
            </button>
        `;
    }

    card.innerHTML = html;
    return card;
}

// ==========================================================================
// 4. Cronómetros en Tiempo Real
// ==========================================================================

function actualizarCronometros() {
    const cronometros = document.querySelectorAll('.posicion-cronometro');
    const ahora = new Date();

    cronometros.forEach(crono => {
        const timestampIngreso = new Date(crono.dataset.timestamp);
        const timestampFin = crono.dataset.timestampFin;
        
        const tiempoFin = timestampFin ? new Date(timestampFin) : ahora;
        const diferenciaSegundos = Math.max(0, Math.floor((tiempoFin - timestampIngreso) / 1000));
        
        const horas = Math.floor(diferenciaSegundos / 3600);
        const minutos = Math.floor((diferenciaSegundos % 3600) / 60);
        const segundos = diferenciaSegundos % 60;
        
        const tiempoStr = `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`;
        
        if (timestampFin) {
            crono.className = 'posicion-cronometro crono-detenido';
            crono.innerHTML = `⏹️ ${tiempoStr}`;
        } else {
            const minutosTotales = diferenciaSegundos / 60;
            if (minutosTotales >= 60) {
                crono.className = 'posicion-cronometro crono-critico';
            } else if (minutosTotales >= 30) {
                crono.className = 'posicion-cronometro crono-alerta';
            } else {
                crono.className = 'posicion-cronometro crono-normal';
            }
            crono.innerHTML = `⏱️ ${tiempoStr}`;
        }
    });
}

// ==========================================================================
// 5. Gestión de Modales
// ==========================================================================

function abrirModal(pos) {
    posicionSeleccionada = pos;
    document.getElementById('modal-posicion-id').textContent = pos.id;
    document.getElementById('select-estado').value = pos.estado;
    
    const inputPaciente = document.getElementById('input-paciente');
    const selectDestino = document.getElementById('select-destino-ocupado');
    
    inputPaciente.value = pos.nombre_paciente || '';
    selectDestino.value = pos.destino_solicitado || '';

    actualizarCamposOcupado();
    document.getElementById('modalEstado').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modalEstado').classList.remove('active');
    posicionSeleccionada = null;
}

function actualizarCamposOcupado() {
    const estado = document.getElementById('select-estado').value;
    const grupoPaciente = document.getElementById('grupo-paciente');
    const grupoDestino = document.getElementById('grupo-destino');
    
    if (estado === 'OCUPADO') {
        grupoPaciente.style.display = 'block';
        grupoDestino.style.display = 'block';
    } else {
        grupoPaciente.style.display = 'none';
        grupoDestino.style.display = 'none';
    }
}

document.getElementById('select-estado').addEventListener('change', actualizarCamposOcupado);

async function guardarEstado() {
    if (!posicionSeleccionada) return;

    const nuevoEstado = document.getElementById('select-estado').value;
    const nombrePaciente = document.getElementById('input-paciente').value.trim();
    const destinoSolicitado = document.getElementById('select-destino-ocupado').value;

    if (nuevoEstado === 'OCUPADO') {
        if (!nombrePaciente) {
            alert('Debe ingresar el nombre del paciente.');
            return;
        }
        if (!destinoSolicitado) {
            alert('Debe seleccionar el destino del paciente.');
            return;
        }
    }

    try {
        const body = {
            estado: nuevoEstado,
            nombre_paciente: nuevoEstado === 'OCUPADO' ? nombrePaciente : '',
            destino_solicitado: nuevoEstado === 'OCUPADO' ? destinoSolicitado : ''
        };

        const response = await fetch(`/api/posiciones/${posicionSeleccionada.id}/estado/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        if (data.success) {
            cerrarModal();
            // Actualización inmediata local
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al guardar estado:', error);
        alert('Error de conexión al guardar el estado');
    }
}

function abrirModalDestino(posicionId) {
    posicionDestinoId = posicionId;
    document.getElementById('modal-destino-posicion-id').textContent = posicionId;
    document.getElementById('select-destino-final').value = '';
    document.getElementById('modalDestino').classList.add('active');
}

function cerrarModalDestino() {
    document.getElementById('modalDestino').classList.remove('active');
    posicionDestinoId = null;
}

async function guardarDestino() {
    const destinoAsignado = document.getElementById('select-destino-final').value;
    if (!destinoAsignado) {
        alert('Debe seleccionar un destino final.');
        return;
    }

    try {
        const response = await fetch(`/api/posiciones/${posicionDestinoId}/marcar-destino/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destino_asignado: destinoAsignado })
        });

        const data = await response.json();
        if (data.success) {
            cerrarModalDestino();
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al marcar destino:', error);
        alert('Error al marcar el destino');
    }
}

// ==========================================================================
// 6. Toasts Flotantes
// ==========================================================================

function mostrarToast(mensaje, tipo = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;
    toast.innerHTML = `<span>${mensaje}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

