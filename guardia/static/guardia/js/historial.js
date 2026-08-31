/**
 * FlowBed - Historial & Analytics Client
 * Renderizado de gráficos interactivos con Chart.js y filtrado de tabla
 */

document.addEventListener('DOMContentLoaded', () => {
    inicializarGraficos();
    inicializarBuscadorTabla();
});

function inicializarGraficos() {
    const rawData = document.getElementById('chart-data-payload');
    if (!rawData) return;

    let chartData;
    try {
        chartData = JSON.parse(rawData.textContent);
    } catch (e) {
        console.error('Error al parsear datos de gráficos:', e);
        return;
    }

    if (!chartData.labels || chartData.labels.length === 0) return;

    // 1. Gráfico de Barras: Tiempos Promedio de Espera
    const ctxBar = document.getElementById('chart-tiempos');
    if (ctxBar && window.Chart) {
        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Tiempo Promedio (minutos)',
                    data: chartData.avg_times,
                    backgroundColor: chartData.colors.map(c => c + 'cc'),
                    borderColor: chartData.colors,
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` Espera promedio: ${context.parsed.y} min`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Minutos' },
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // 2. Gráfico Doughnut: Distribución de Pacientes
    const ctxPie = document.getElementById('chart-distribucion');
    if (ctxPie && window.Chart) {
        new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.counts,
                    backgroundColor: chartData.colors,
                    hoverOffset: 6,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, padding: 14 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const val = context.raw;
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${context.label}: ${val} pacientes (${pct}%)`;
                            }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }
}

function inicializarBuscadorTabla() {
    const input = document.getElementById('table-search-input');
    const tbody = document.getElementById('tabla-historial-body');
    if (!input || !tbody) return;

    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const rows = tbody.querySelectorAll('tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

