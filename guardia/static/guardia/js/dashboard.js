/**
 * FlowBed - Real-Time Dashboard Client
 * Server-Sent Events (SSE), Live Stopwatch, KPI Counters, Search & Filters
 * Circuito Completo: Ingreso -> Solicitud de Cama -> Asignación -> Traslado -> Limpieza -> Libre
 */

let posiciones = [];
let posicionesPreviasMap = new Map();
let posicionSeleccionada = null;
let posicionActivaModal = null;
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
        } else if (previa.etapa_circuito !== nueva.etapa_circuito) {
            if (nueva.etapa_circuito === 'SOLICITADA') {
                mostrarToast(`⏳ <strong>${nueva.id}</strong>: Cama solicitada a ${nueva.destino_solicitado}`, 'warning');
            } else if (nueva.etapa_circuito === 'ASIGNADA') {
                mostrarToast(`✅ <strong>${nueva.id}</strong>: Cama asignada en ${nueva.destino_asignado}`, 'success');
            }
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

    if (pos.estado === 'OCUPADO') {
        if (pos.etapa_circuito === 'ATENCION') {
            html += `<div class="posicion-destino-solicitado" style="color: #475569; background: #f1f5f9;">🩺 En Atención Inicial</div>`;
            html += `</div>`;
            html += `
                <button class="btn-marcar-destino" style="background: #3b82f6;" onclick="event.stopPropagation(); abrirModalSolicitar('${pos.id}')">
                    📋 Solicitar Cama
                </button>
            `;
        } else if (pos.etapa_circuito === 'SOLICITADA') {
            html += `<div class="posicion-destino-solicitado">⏳ Solicitada: ${destinoIconos[pos.destino_solicitado] || pos.destino_solicitado}</div>`;
            
            // Cronómetro de espera por cama
            const timestampInicioCrono = pos.timestamp_solicitud || pos.timestamp_ingreso;
            html += `<div class="posicion-cronometro crono-normal" data-timestamp="${timestampInicioCrono}" data-timestamp-fin="">⏱️ Espera: 00:00:00</div>`;
            html += `</div>`;
            html += `
                <button class="btn-marcar-destino" style="background: #10b981;" onclick="event.stopPropagation(); abrirModalAceptar('${pos.id}')">
                    ✅ Aceptar / Asignar Cama
                </button>
            `;
        } else if (pos.etapa_circuito === 'ASIGNADA') {
            const detalleCama = pos.cama_asignada_detalle ? ` (${pos.cama_asignada_detalle})` : '';
            html += `<div class="posicion-destino-asignado">✅ Asignada: ${pos.destino_asignado}${detalleCama}</div>`;
            
            // Cronómetro detenido de espera de cama
            const timestampInicioCrono = pos.timestamp_solicitud || pos.timestamp_ingreso;
            const timestampFin = pos.timestamp_destino_asignado;
            html += `<div class="posicion-cronometro crono-detenido" data-timestamp="${timestampInicioCrono}" data-timestamp-fin="${timestampFin || ''}">⏹️ Espera: 00:00:00</div>`;
            html += `</div>`;
            html += `
                <button class="btn-marcar-destino" style="background: #f59e0b; color: #ffffff;" onclick="event.stopPropagation(); abrirModalTraslado('${pos.id}')">
                    🚚 Confirmar Traslado
                </button>
            `;
        }
    } else if (pos.estado === 'LIMPIEZA') {
        html += `<div class="posicion-destino-solicitado" style="color: #d97706; background: #fffbeb;">🧹 Desinfección / Higiene</div>`;
        html += `</div>`;
        html += `
            <button class="btn-marcar-destino" style="background: #10b981;" onclick="event.stopPropagation(); marcarLimpiezaCompletada('${pos.id}')">
                ✨ Limpieza Lista ➔ Libre
            </button>
        `;
    } else {
        html += `</div>`;
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
        const rawTs = crono.dataset.timestamp;
        if (!rawTs) return;

        const timestampIngreso = new Date(rawTs);
        const timestampFin = crono.dataset.timestampFin;
        
        const tiempoFin = timestampFin ? new Date(timestampFin) : ahora;
        const diferenciaSegundos = Math.max(0, Math.floor((tiempoFin - timestampIngreso) / 1000));
        
        const horas = Math.floor(diferenciaSegundos / 3600);
        const minutos = Math.floor((diferenciaSegundos % 3600) / 60);
        const segundos = diferenciaSegundos % 60;
        
        const tiempoStr = `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segundos).padStart(2, '0')}`;
        
        if (timestampFin) {
            crono.className = 'posicion-cronometro crono-detenido';
            crono.innerHTML = `⏹️ Espera: ${tiempoStr}`;
        } else {
            const minutosTotales = diferenciaSegundos / 60;
            if (minutosTotales >= 60) {
                crono.className = 'posicion-cronometro crono-critico';
            } else if (minutosTotales >= 30) {
                crono.className = 'posicion-cronometro crono-alerta';
            } else {
                crono.className = 'posicion-cronometro crono-normal';
            }
            crono.innerHTML = `⏱️ Espera: ${tiempoStr}`;
        }
    });
}

// ==========================================================================
// 5. Gestión de Modales y Circuito
// ==========================================================================

// Modal General
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

    if (nuevoEstado === 'OCUPADO' && !nombrePaciente) {
        alert('Debe ingresar el nombre del paciente.');
        return;
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

// Paso 1: Modal Solicitar Cama
function abrirModalSolicitar(posicionId) {
    const pos = posiciones.find(p => p.id === posicionId);
    if (!pos) return;

    posicionActivaModal = pos;
    document.getElementById('modal-solicitar-posicion-id').textContent = pos.id;
    document.getElementById('modal-solicitar-paciente-nombre').textContent = pos.nombre_paciente || 'Paciente';
    document.getElementById('select-solicitar-destino').value = '';
    document.getElementById('modalSolicitarCama').classList.add('active');
}

function cerrarModalSolicitar() {
    document.getElementById('modalSolicitarCama').classList.remove('active');
    posicionActivaModal = null;
}

async function enviarSolicitudCama() {
    if (!posicionActivaModal) return;

    const destino = document.getElementById('select-solicitar-destino').value;
    if (!destino) {
        alert('Debe seleccionar el sector requerido para el paciente.');
        return;
    }

    try {
        const response = await fetch(`/api/posiciones/${posicionActivaModal.id}/solicitar-cama/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destino_solicitado: destino })
        });

        const data = await response.json();
        if (data.success) {
            cerrarModalSolicitar();
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al solicitar cama:', error);
        alert('Error de conexión al solicitar cama');
    }
}

// Paso 2: Modal Aceptar / Asignar Cama
function abrirModalAceptar(posicionId) {
    const pos = posiciones.find(p => p.id === posicionId);
    if (!pos) return;

    posicionActivaModal = pos;
    document.getElementById('modal-aceptar-posicion-id').textContent = pos.id;
    document.getElementById('modal-aceptar-paciente-nombre').textContent = pos.nombre_paciente || 'Paciente';
    document.getElementById('select-aceptar-destino').value = pos.destino_solicitado || 'PISO';
    document.getElementById('input-cama-detalle').value = '';
    document.getElementById('modalAceptarAsignar').classList.add('active');
}

function cerrarModalAceptar() {
    document.getElementById('modalAceptarAsignar').classList.remove('active');
    posicionActivaModal = null;
}

async function confirmarAsignacionCama() {
    if (!posicionActivaModal) return;

    const destino = document.getElementById('select-aceptar-destino').value;
    const camaDetalle = document.getElementById('input-cama-detalle').value.trim();

    if (!destino) {
        alert('Debe seleccionar el sector asignado.');
        return;
    }

    try {
        const response = await fetch(`/api/posiciones/${posicionActivaModal.id}/aceptar-asignar/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                destino_asignado: destino,
                cama_asignada_detalle: camaDetalle
            })
        });

        const data = await response.json();
        if (data.success) {
            cerrarModalAceptar();
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al confirmar asignación:', error);
        alert('Error de conexión al confirmar asignación');
    }
}

// Paso 3: Modal Confirmar Traslado
function abrirModalTraslado(posicionId) {
    const pos = posiciones.find(p => p.id === posicionId);
    if (!pos) return;

    posicionActivaModal = pos;
    document.getElementById('modal-traslado-posicion-id').textContent = pos.id;
    document.getElementById('modal-traslado-paciente-nombre').textContent = pos.nombre_paciente || 'Paciente';
    
    const detalleCama = pos.cama_asignada_detalle ? ` (${pos.cama_asignada_detalle})` : '';
    document.getElementById('modal-traslado-destino-info').textContent = `${pos.destino_asignado || 'Piso'}${detalleCama}`;
    
    document.getElementById('select-traslado-siguiente-estado').value = 'LIMPIEZA';
    document.getElementById('modalTraslado').classList.add('active');
}

function cerrarModalTraslado() {
    document.getElementById('modalTraslado').classList.remove('active');
    posicionActivaModal = null;
}

async function confirmarTrasladoPaciente() {
    if (!posicionActivaModal) return;

    const siguienteEstado = document.getElementById('select-traslado-siguiente-estado').value;

    try {
        const response = await fetch(`/api/posiciones/${posicionActivaModal.id}/trasladar-egresar/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ siguiente_estado: siguienteEstado })
        });

        const data = await response.json();
        if (data.success) {
            cerrarModalTraslado();
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al trasladar paciente:', error);
        alert('Error de conexión al confirmar traslado');
    }
}

// Limpieza Lista -> Libre
async function marcarLimpiezaCompletada(posicionId) {
    try {
        const response = await fetch(`/api/posiciones/${posicionId}/limpieza-completada/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        if (data.success) {
            cargarPosicionesFallback();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al completar limpieza:', error);
        alert('Error al completar limpieza');
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


