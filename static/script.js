// Global variables
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let calendarData = {};
let despesasData = [];

// Calendar functionality
function initCalendar() {
    loadCalendarData();
    setupCalendarEvents();
    renderCalendar();
}

function setupCalendarEvents() {
    document.getElementById('btn-prev-month').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        loadCalendarData();
        renderCalendar();
    });

    document.getElementById('btn-next-month').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        loadCalendarData();
        renderCalendar();
    });

    // Modal events
    const modal = document.getElementById('modal-edit-day');
    const closeBtn = modal.querySelector('.close');

    closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.getElementById('form-edit-day').addEventListener('submit', saveCalendarDay);
}

function loadCalendarData() {
    fetch(`/api/calendario/${currentYear}/${currentMonth + 1}`)
        .then(response => response.json())
        .then(data => {
            calendarData = data;
            renderCalendar();
        })
        .catch(error => console.error('Error loading calendar data:', error));
}

function renderCalendar() {
    const monthNames = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];

    document.getElementById('calendar-title').textContent = 
        `${monthNames[currentMonth]} ${currentYear}`;

    // Update analytics
    const analytics = calculateCalendarAnalytics();
    updateCalendarAnalytics(analytics);

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const calendarDays = document.getElementById('calendar-days');

    calendarDays.innerHTML = '';

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day other-month';
        calendarDays.appendChild(dayElement);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';

        const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayData = calendarData[dateStr];
        const dayOfWeek = new Date(currentYear, currentMonth, day).getDay();
        const holidayName = isNationalHoliday(currentYear, currentMonth, day);

        // Check if it's weekend (Saturday = 6, Sunday = 0)
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            dayElement.classList.add('weekend');
        }

        // Check if it's a national holiday
        if (holidayName && !dayData) {
            dayElement.classList.add('feriado');
        }

        if (dayData) {
            dayElement.classList.add(dayData.responsavel);
        }

        const displayInfo = dayData ? getResponsavelName(dayData.responsavel) : (holidayName || '');

        dayElement.innerHTML = `
            <div class="day-number">${day}</div>
            <div class="day-info">${displayInfo}</div>
        `;

        dayElement.addEventListener('click', () => openEditModal(dateStr, dayData));
        calendarDays.appendChild(dayElement);
    }
}

function updateCalendarAnalytics(analytics) {
    const analyticsContainer = document.getElementById('calendar-analytics');
    if (analyticsContainer) {
        analyticsContainer.innerHTML = `
            <div class="analytics-item">
                <span class="analytics-label">Leonardo:</span>
                <span class="analytics-value">${analytics.leonardo.realizado} realizados, ${analytics.leonardo.planejado} planejados</span>
            </div>
            <div class="analytics-item">
                <span class="analytics-label">Taciana:</span>
                <span class="analytics-value">${analytics.taciana.realizado} realizados, ${analytics.taciana.planejado} planejados</span>
            </div>
            <div class="analytics-item">
                <span class="analytics-label">Avós:</span>
                <span class="analytics-value">${analytics.avos_paternos.realizado} realizados, ${analytics.avos_paternos.planejado} planejados</span>
            </div>
        `;
    }
}

function getResponsavelName(responsavel) {
    const names = {
        'leonardo': 'Leonardo',
        'taciana': 'Taciana', 
        'avos_paternos': 'Avós',
        'feriado': 'Feriado'
    };
    return names[responsavel] || '';
}

function isNationalHoliday(year, month, day) {
    const feriados = {
        '01-01': 'Confraternização Universal',
        '04-21': 'Tiradentes',
        '05-01': 'Dia do Trabalhador',
        '09-07': 'Independência do Brasil',
        '10-12': 'Nossa Senhora Aparecida',
        '11-02': 'Finados',
        '11-15': 'Proclamação da República',
        '12-25': 'Natal'
    };
    
    const dateKey = `${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    
    // Check fixed holidays
    if (feriados[dateKey]) {
        return feriados[dateKey];
    }
    
    // Calculate Easter and related holidays
    const easter = calculateEaster(year);
    const carnaval = new Date(easter.getTime() - 47 * 24 * 60 * 60 * 1000); // 47 days before Easter
    const sextaFeira = new Date(easter.getTime() - 2 * 24 * 60 * 60 * 1000); // Good Friday
    const corpusChristi = new Date(easter.getTime() + 60 * 24 * 60 * 60 * 1000); // 60 days after Easter
    
    const currentDate = new Date(year, month, day);
    
    if (isSameDate(currentDate, carnaval) || isSameDate(currentDate, new Date(carnaval.getTime() + 24 * 60 * 60 * 1000))) {
        return 'Carnaval';
    }
    if (isSameDate(currentDate, sextaFeira)) {
        return 'Sexta-feira Santa';
    }
    if (isSameDate(currentDate, corpusChristi)) {
        return 'Corpus Christi';
    }
    
    return null;
}

function calculateEaster(year) {
    const a = year % 19;
    const b = Math.floor(year / 100);
    const c = year % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31);
    const day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(year, month - 1, day);
}

function isSameDate(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
}

function openEditModal(date, dayData) {
    document.getElementById('edit-date').value = date;
    document.getElementById('edit-responsavel').value = dayData ? dayData.responsavel : 'leonardo';
    document.getElementById('edit-tipo').value = dayData ? dayData.tipo : 'planejado';
    document.getElementById('edit-observacao').value = dayData ? dayData.observacao || '' : '';

    document.getElementById('modal-edit-day').style.display = 'block';
}

function closeModal() {
    document.getElementById('modal-edit-day').style.display = 'none';
}

function saveCalendarDay(e) {
    e.preventDefault();

    const data = {
        data: document.getElementById('edit-date').value,
        responsavel: document.getElementById('edit-responsavel').value,
        tipo: document.getElementById('edit-tipo').value,
        observacao: document.getElementById('edit-observacao').value
    };

    fetch('/api/calendario/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.sucesso) {
            closeModal();
            loadCalendarData();
        } else {
            alert('Erro ao salvar: ' + (result.erro || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        console.error('Error saving calendar data:', error);
        alert('Erro ao salvar dados do calendário');
    });
}

// Financial account functionality
function initConta() {
    loadDespesas();
    setupContaEvents();
}

function setupContaEvents() {
    document.getElementById('btn-nova-despesa').addEventListener('click', openNovaDespesaModal);

    // View toggle events
    //document.getElementById('btn-view-list').addEventListener('click', () => toggleView('list'));
    //document.getElementById('btn-view-table').addEventListener('click', () => toggleView('table'));

    // Modal events
    const modal = document.getElementById('modal-despesa');
    const closeBtn = modal.querySelector('.close');

    closeBtn.addEventListener('click', closeModalDespesa);
    window.addEventListener('click', (e) => {
        if (e.target === modal) closeModalDespesa();
    });

    document.getElementById('form-despesa').addEventListener('submit', saveDespesa);

    // Type change event
    document.getElementById('despesa-tipo').addEventListener('change', toggleTipoFields);

    // Filter events
    document.getElementById('filter-descricao').addEventListener('input', filterDespesas);
    document.getElementById('filter-categoria').addEventListener('change', filterDespesas);
    document.getElementById('filter-status').addEventListener('change', filterDespesas);
    document.getElementById('filter-mes').addEventListener('change', filterDespesas);

    // Set default date to today
    document.getElementById('despesa-data').value = new Date().toISOString().split('T')[0];
}

function loadDespesas() {
    fetch('/api/despesas')
        .then(response => response.json())
        .then(data => {
            despesasData = data;
            populateMonthFilter();
            renderDespesasTabela();
            updateResumoFinanceiro();
        })
        .catch(error => console.error('Error loading expenses:', error));
}

function populateMonthFilter() {
    const months = [...new Set(despesasData.map(d => d.data.substring(0, 7)))].sort();
    const filterMes = document.getElementById('filter-mes');

    // Clear existing options except the first one
    filterMes.innerHTML = '<option value="">Todos os meses</option>';

    months.forEach(month => {
        const [year, monthNum] = month.split('-');
        const monthNames = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ];
        const monthName = monthNames[parseInt(monthNum) - 1];
        const option = document.createElement('option');
        option.value = month;
        option.textContent = `${monthName} ${year}`;
        filterMes.appendChild(option);
    });
}



function renderDespesasTabela() {
    const container = document.getElementById('despesas-tabela');

    // Group expenses by month
    const groupedByMonth = {};
    despesasData.forEach(despesa => {
        const month = despesa.data.substring(0, 7);
        if (!groupedByMonth[month]) {
            groupedByMonth[month] = [];
        }
        groupedByMonth[month].push(despesa);
    });

    const monthNames = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];

    // Get current month
    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

    // Sort months: current first, then future months ascending, then past months descending
    const sortedMonths = Object.keys(groupedByMonth).sort((a, b) => {
        // Current month always comes first
        if (a === currentMonth && b !== currentMonth) return -1;
        if (b === currentMonth && a !== currentMonth) return 1;
        if (a === currentMonth && b === currentMonth) return 0;
        
        const aIsFuture = a > currentMonth;
        const bIsFuture = b > currentMonth;
        
        // If one is future and other is past, future comes first
        if (aIsFuture && !bIsFuture) return -1;
        if (!aIsFuture && bIsFuture) return 1;
        
        // If both are future, sort ascending (nearest first)
        if (aIsFuture && bIsFuture) {
            return a.localeCompare(b);
        }
        
        // If both are past, sort descending (most recent first)
        return b.localeCompare(a);
    });

    let html = '';

    sortedMonths.forEach(month => {
        const [year, monthNum] = month.split('-');
        const monthName = monthNames[parseInt(monthNum) - 1];
        const expenses = groupedByMonth[month];

        const totalMonth = expenses.filter(d => d.status === 'validado').reduce((sum, d) => sum + d.valor, 0);

        html += `
            <div class="month-section">
                <h3>${monthName} ${year} - Total: ${formatCurrency(totalMonth)}</h3>
                <div class="table-container">
                    <table class="despesas-table">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Descrição</th>
                                <th>Pagador</th>
                                <th>Categoria</th>
                                <th>Valor</th>
                                <th>Tipo</th>
                                <th>Status</th>
                                <th>Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${expenses.map(despesa => `
                                <tr class="pagador-${despesa.pagador}">
                                    <td>${formatDate(despesa.data)}</td>
                                    <td>
                                        ${despesa.descricao}
                                        ${despesa.anexo ? `<span class="anexo-icon" onclick="showAnexo('${despesa.anexo}')" title="Visualizar anexo">🔗</span>` : ''}
                                    </td>
                                    <td>${despesa.pagador === 'leonardo' ? 'Leonardo' : 'Taciana'}</td>
                                    <td>${capitalizeFirst(despesa.categoria)}</td>
                                    <td>${formatCurrency(despesa.valor)}</td>
                                    <td>${getTipoDescricao(despesa)}</td>
                                    <td>
                                        <span class="status-badge status-${despesa.status}">
                                            ${despesa.status === 'pendente' ? 'Pendente' : 'Validado'}
                                        </span>
                                    </td>
                                    <td>
                                        ${despesa.status === 'pendente' ? 
                                            `<button class="btn-success btn-small" onclick="validarDespesa(${despesa.id})">Validar</button>` : 
                                            `<small>Por: ${despesa.validado_por}</small>`
                                        }
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    container.innerHTML = html || '<div style="padding: 40px; text-align: center; color: #666;">Nenhuma despesa encontrada</div>';
}

function getTipoDescricao(despesa) {
    if (despesa.tipo === 'parcelada') {
        return `Parcela ${despesa.parcela_atual}/${despesa.parcelas_total}`;
    } else if (despesa.tipo === 'recorrente') {
        return 'Recorrente';
    }
    return 'Única';
}



function updateResumoFinanceiro() {
    // Função mantida apenas para calcular resumo por categorias se necessário
    updateResumoCategorias();
}

function updateResumoCategorias() {
    const categorias = {};
    const currentYear = new Date().getFullYear();
    
    despesasData
        .filter(d => d.status === 'validado' && d.data.startsWith(currentYear.toString()))
        .forEach(despesa => {
            if (!categorias[despesa.categoria]) {
                categorias[despesa.categoria] = 0;
            }
            categorias[despesa.categoria] += despesa.valor;
        });

    const resumoContainer = document.getElementById('resumo-categorias');
    if (resumoContainer) {
        resumoContainer.innerHTML = Object.entries(categorias)
            .sort(([,a], [,b]) => b - a)
            .map(([categoria, total]) => `
                <div class="categoria-item">
                    <h4>${capitalizeFirst(categoria)}</h4>
                    <div class="categoria-valor">${formatCurrency(total)}</div>
                </div>
            `).join('');
    }
}

function openNovaDespesaModal() {
    document.getElementById('modal-title').textContent = 'Nova Despesa';
    document.getElementById('form-despesa').reset();
    document.getElementById('despesa-data').value = new Date().toISOString().split('T')[0];
    toggleTipoFields();
    document.getElementById('modal-despesa').style.display = 'block';
}

function closeModalDespesa() {
    document.getElementById('modal-despesa').style.display = 'none';
}

function toggleTipoFields() {
    const tipo = document.getElementById('despesa-tipo').value;
    const parcelamentoFields = document.getElementById('parcelamento-fields');
    const recorrenciaFields = document.getElementById('recorrencia-fields');

    parcelamentoFields.classList.toggle('hidden', tipo !== 'parcelada');
    recorrenciaFields.classList.toggle('hidden', tipo !== 'recorrente');
}

async function saveDespesa(e) {
    e.preventDefault();

    const formData = new FormData();
    const anexoFile = document.getElementById('despesa-anexo').files[0];
    let anexoFilename = null;

    // Upload file if present
    if (anexoFile) {
        formData.append('arquivo', anexoFile);

        try {
            const uploadResponse = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const uploadResult = await uploadResponse.json();

            if (uploadResult.sucesso) {
                anexoFilename = uploadResult.filename;
            } else {
                alert('Erro ao fazer upload do arquivo: ' + uploadResult.erro);
                return;
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            alert('Erro ao fazer upload do arquivo');
            return;
        }
    }

    const data = {
        data: document.getElementById('despesa-data').value,
        descricao: document.getElementById('despesa-descricao').value,
        valor: parseFloat(document.getElementById('despesa-valor').value),
        pagador: document.getElementById('despesa-pagador').value,
        categoria: document.getElementById('despesa-categoria').value,
        tipo: document.getElementById('despesa-tipo').value,
        anexo: anexoFilename,
        auto_validar: document.getElementById('despesa-tipo').value === 'recorrente'
    };

    if (data.tipo === 'parcelada') {
        data.parcelas_total = parseInt(document.getElementById('parcelas-total').value);
        data.parcela_atual = parseInt(document.getElementById('parcela-atual').value);
    } else if (data.tipo === 'recorrente') {
        data.recorrente_ate = document.getElementById('recorrente-ate').value;
    }

    fetch('/api/despesas/salvar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.sucesso) {
            closeModalDespesa();
            loadDespesas();
        } else {
            alert('Erro ao salvar: ' + (result.erro || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        console.error('Error saving expense:', error);
        alert('Erro ao salvar despesa');
    });
}

function validarDespesa(despesaId) {
    if (!confirm('Confirma a validação desta despesa?')) return;

    fetch(`/api/despesas/validar/${despesaId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.sucesso) {
            loadDespesas();
        } else {
            alert('Erro ao validar despesa: ' + (result.erro || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        console.error('Error validating expense:', error);
        alert('Erro ao validar despesa');
    });
}

function filterDespesas() {
    const descricaoFilter = document.getElementById('filter-descricao').value.toLowerCase();
    const categoriaFilter = document.getElementById('filter-categoria').value;
    const statusFilter = document.getElementById('filter-status').value;
    const mesFilter = document.getElementById('filter-mes').value;

    const filtered = despesasData.filter(despesa => {
        const matchDescricao = !descricaoFilter || despesa.descricao.toLowerCase().includes(descricaoFilter);
        const matchCategoria = !categoriaFilter || despesa.categoria === categoriaFilter;
        const matchStatus = !statusFilter || despesa.status === statusFilter;
        const matchMes = !mesFilter || despesa.data.startsWith(mesFilter);

        return matchDescricao && matchCategoria && matchStatus && matchMes;
    });

    const isTableView = document.getElementById('despesas-tabela').style.display !== 'none';
    if (isTableView) {
        // For table view, we need to update the global data and re-render
        const originalData = despesasData;
        despesasData = filtered;
        renderDespesasTabela();
        despesasData = originalData;
    } else {
        renderDespesasTabela(filtered);
    }
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('pt-BR');
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function calculateCalendarAnalytics() {
    const analytics = {
        leonardo: { planejado: 0, realizado: 0 },
        taciana: { planejado: 0, realizado: 0 },
        avos_paternos: { planejado: 0, realizado: 0 }
    };

    const today = new Date();
    const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

    for (const [date, info] of Object.entries(calendarData)) {
        if (date.startsWith(currentMonth)) {
            const dayDate = new Date(date + 'T00:00:00');
            const responsavel = info.responsavel;

            if (analytics[responsavel]) {
                if (dayDate <= today) {
                    analytics[responsavel].realizado++;
                } else {
                    analytics[responsavel].planejado++;
                }
            }
        }
    }

    return analytics;
}

function showAnexo(filename) {
    const modal = createAnexoModal();
    const modalContent = modal.querySelector('.anexo-modal-content');
    
    // Determine file type
    const fileExtension = filename.split('.').pop().toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension)) {
        modalContent.innerHTML = `
            <span class="close-anexo" onclick="closeAnexoModal()">&times;</span>
            <img src="/static/uploads/${filename}" alt="Anexo">
        `;
    } else if (fileExtension === 'pdf') {
        modalContent.innerHTML = `
            <span class="close-anexo" onclick="closeAnexoModal()">&times;</span>
            <iframe src="/static/uploads/${filename}" width="100%" height="500px"></iframe>
        `;
    } else {
        modalContent.innerHTML = `
            <span class="close-anexo" onclick="closeAnexoModal()">&times;</span>
            <div style="text-align: center; padding: 50px;">
                <p>Arquivo não pode ser visualizado no navegador</p>
                <a href="/static/uploads/${filename}" download class="btn-primary">Download</a>
            </div>
        `;
    }
    
    modal.style.display = 'block';
}

function createAnexoModal() {
    let modal = document.getElementById('anexo-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'anexo-modal';
        modal.className = 'anexo-modal';
        modal.innerHTML = '<div class="anexo-modal-content"></div>';
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAnexoModal();
        });
    }
    return modal;
}

function closeAnexoModal() {
    const modal = document.getElementById('anexo-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}
