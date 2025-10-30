/**
 * TechHelp Dashboard - JavaScript Principal
 * Gerencia a interface do usuário, gráficos e integração com a API
 */

class TechHelpDashboard {
    constructor() {
        this.apiBaseUrl = this.getApiUrl();
        this.data = null;
        this.charts = {};
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.filteredData = [];
        
        this.init();
    }

    /**
     * Determina a URL base da API baseada no ambiente
     */
    getApiUrl() {
        const hostname = window.location.hostname;
        
        // Para desenvolvimento local
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Usar 5001 em desenvolvimento para evitar conflitos
            return 'http://localhost:5001';
        }
        
        // Para produção, assume que a API está no mesmo domínio ou configurada
        return window.location.origin.replace(':8080', ':5000') || 'https://your-api-domain.com';
    }

    /**
     * Inicializa o dashboard
     */
    async init() {
        try {
            this.showLoading(true);
            this.setupEventListeners();
            await this.loadData();
            this.hideLoading();
        } catch (error) {
            console.error('Erro na inicialização:', error);
            this.hideLoading();
            this.showError('Erro ao inicializar dashboard', error.message);
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Botão de atualizar
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Fechamento de erro
        const closeError = document.getElementById('close-error');
        if (closeError) {
            closeError.addEventListener('click', () => this.hideError());
        }

        // Filtros da tabela
        const searchInput = document.getElementById('search-input');
        const statusFilter = document.getElementById('status-filter');
        
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterTable());
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterTable());
        }

        // Paginação
        const prevPage = document.getElementById('prev-page');
        const nextPage = document.getElementById('next-page');
        
        if (prevPage) {
            prevPage.addEventListener('click', () => this.previousPage());
        }
        
        if (nextPage) {
            nextPage.addEventListener('click', () => this.nextPage());
        }

        // Redimensionamento da janela
        window.addEventListener('resize', () => this.resizeCharts());
    }

    /**
     * Carrega dados da API
     */
    async loadData() {
        try {
            console.log('🔄 Carregando dados da API...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/chamados`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Adiciona timeout
                signal: AbortSignal.timeout(15000)
            });

            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
            }

            this.data = await response.json();
            
            // Verifica se há warning (dados podem estar desatualizados)
            if (this.data.warning) {
                this.showWarning(this.data.warning);
            }
            
            // Verifica se está em modo demonstração
            if (this.data.modo_demonstracao && this.data.aviso) {
                this.showWarning(this.data.aviso);
            }

            console.log('✅ Dados carregados:', this.data);
            
            this.updateDashboard();
            
        } catch (error) {
            console.error('❌ Erro ao carregar dados:', error);
            
            // Se for erro de conexão, tenta usar dados de fallback
            if (error.name === 'TypeError' || error.name === 'TimeoutError') {
                this.loadFallbackData();
            } else {
                throw error;
            }
        }
    }

    /**
     * Carrega dados de fallback para demonstração
     */
    loadFallbackData() {
        console.log('⚠️ Carregando dados de demonstração...');
        
        this.data = {
            total_chamados: 45,
            total_abertos: 12,
            total_fechados: 33,
            tempo_medio_resolucao: '2.3 horas',
            chamados_por_tecnico: {
                'João Silva': 14,
                'Maria Santos': 12,
                'Carlos Oliveira': 10,
                'Ana Costa': 9
            },
            categorias: {
                'Hardware': 18,
                'Software': 12,
                'Rede': 8,
                'Sistema': 7
            },
            tabela: [
                { id: '001', tecnico: 'João Silva', categoria: 'Hardware', status: 'Fechado', satisfacao: 5 },
                { id: '002', tecnico: 'Maria Santos', categoria: 'Software', status: 'Aberto', satisfacao: 'N/A' },
                { id: '003', tecnico: 'Carlos Oliveira', categoria: 'Rede', status: 'Fechado', satisfacao: 4 },
                { id: '004', tecnico: 'Ana Costa', categoria: 'Sistema', status: 'Fechado', satisfacao: 5 },
                { id: '005', tecnico: 'João Silva', categoria: 'Hardware', status: 'Em Andamento', satisfacao: 'N/A' }
            ],
            insights: {
                melhor_tecnico: '🏆 João Silva foi o técnico mais produtivo com 14 chamados resolvidos.',
                categoria_predominante: '📈 Hardware representa 40.0% dos chamados (18 ocorrências).',
                tendencia_satisfacao: '😊 Excelente! Satisfação média de 4.7/5 - clientes muito satisfeitos.'
            },
            ultima_atualizacao: new Date().toLocaleString('pt-BR'),
            warning: 'Dados de demonstração - API não disponível'
        };

        this.updateDashboard();
        this.showWarning('Utilizando dados de demonstração. Verifique a conexão com a API.');
    }

    /**
     * Atualiza o dashboard com os dados carregados
     */
    updateDashboard() {
        this.updateKPIs();
        this.updateCharts();
        this.updateTable();
        this.updateInsights();
        this.updateLastUpdate();
    }

    /**
     * Atualiza os KPIs
     */
    updateKPIs() {
        const elements = {
            'total-chamados': this.data.total_chamados,
            'total-abertos': this.data.total_abertos,
            'total-fechados': this.data.total_fechados,
            'tempo-medio': this.data.tempo_medio_resolucao
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                // Adiciona animação de contagem para números
                if (typeof value === 'number') {
                    this.animateCounter(element, value);
                } else {
                    element.textContent = value;
                }
            }
        });
    }

    /**
     * Anima contador numérico
     */
    animateCounter(element, targetValue) {
        const startValue = 0;
        const duration = 1000;
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = Math.floor(startValue + (targetValue - startValue) * progress);
            element.textContent = currentValue.toLocaleString('pt-BR');

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };

        requestAnimationFrame(updateCounter);
    }

    /**
     * Atualiza os gráficos
     */
    updateCharts() {
        this.createTechniciansChart();
        this.createCategoriesChart();
    }

    /**
     * Cria gráfico de técnicos
     */
    createTechniciansChart() {
        const ctx = document.getElementById('technicians-chart');
        if (!ctx) return;

        // Destrói gráfico anterior se existir
        if (this.charts.technicians) {
            this.charts.technicians.destroy();
        }

        const data = this.data.chamados_por_tecnico;
        const labels = Object.keys(data);
        const values = Object.values(data);

        this.charts.technicians = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Chamados Resolvidos',
                    data: values,
                    backgroundColor: [
                        '#3373dc',
                        '#4285f4',
                        '#34a853',
                        '#fbbc04',
                        '#ea4335'
                    ].slice(0, labels.length),
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: '#3373dc',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y} chamados`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: '#5f6368'
                        },
                        grid: {
                            color: '#e8eaed'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#5f6368',
                            maxRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    /**
     * Cria gráfico de categorias
     */
    createCategoriesChart() {
        const ctx = document.getElementById('categories-chart');
        if (!ctx) return;

        // Destrói gráfico anterior se existir
        if (this.charts.categories) {
            this.charts.categories.destroy();
        }

        const data = this.data.categorias;
        const labels = Object.keys(data);
        const values = Object.values(data);

        this.charts.categories = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#3373dc',
                        '#34a853',
                        '#fbbc04',
                        '#ea4335',
                        '#9aa0a6'
                    ].slice(0, labels.length),
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
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            color: '#5f6368'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: '#3373dc',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Atualiza a tabela
     */
    updateTable() {
        this.filteredData = [...this.data.tabela];
        this.renderTable();
    }

    /**
     * Filtra a tabela
     */
    filterTable() {
        const searchTerm = document.getElementById('search-input')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('status-filter')?.value.toLowerCase() || '';

        this.filteredData = this.data.tabela.filter(item => {
            const matchesSearch = !searchTerm || 
                Object.values(item).some(value => 
                    value.toString().toLowerCase().includes(searchTerm)
                );
            
            const matchesStatus = !statusFilter || 
                item.status.toLowerCase().includes(statusFilter);

            return matchesSearch && matchesStatus;
        });

        this.currentPage = 1;
        this.renderTable();
    }

    /**
     * Renderiza a tabela
     */
    renderTable() {
        const tbody = document.getElementById('table-body');
        if (!tbody) return;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = this.filteredData.slice(startIndex, endIndex);

        if (pageData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading-row">Nenhum chamado encontrado</td></tr>';
        } else {
            tbody.innerHTML = pageData.map(item => `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.tecnico}</td>
                    <td>${item.categoria}</td>
                    <td><span class="status-badge status-${item.status.toLowerCase().replace(' ', '-')}">${item.status}</span></td>
                    <td>${this.formatSatisfaction(item.satisfacao)}</td>
                </tr>
            `).join('');
        }

        this.updatePagination();
    }

    /**
     * Formata a satisfação
     */
    formatSatisfaction(value) {
        if (value === 'N/A' || value === null || value === undefined) {
            return '<span class="text-muted">N/A</span>';
        }
        
        const rating = parseInt(value);
        if (isNaN(rating)) return '<span class="text-muted">N/A</span>';
        
        const stars = '⭐'.repeat(rating);
        const color = rating >= 4 ? 'text-success' : rating >= 3 ? 'text-warning' : 'text-error';
        
        return `<span class="${color}">${stars} (${rating}/5)</span>`;
    }

    /**
     * Atualiza a paginação
     */
    updatePagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (prevBtn) {
            prevBtn.disabled = this.currentPage === 1;
        }

        if (nextBtn) {
            nextBtn.disabled = this.currentPage === totalPages || totalPages === 0;
        }

        if (pageInfo) {
            pageInfo.textContent = `Página ${this.currentPage} de ${totalPages || 1}`;
        }
    }

    /**
     * Página anterior
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderTable();
        }
    }

    /**
     * Próxima página
     */
    nextPage() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderTable();
        }
    }

    /**
     * Atualiza os insights
     */
    updateInsights() {
        const insights = this.data.insights;
        
        const elements = {
            'technicians-insight': insights.melhor_tecnico,
            'categories-insight': insights.categoria_predominante,
            'satisfaction-insight': insights.tendencia_satisfacao
        };

        Object.entries(elements).forEach(([id, text]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = text;
            }
        });
    }

    /**
     * Atualiza timestamp da última atualização
     */
    updateLastUpdate() {
        const element = document.getElementById('last-update-time');
        if (element && this.data.ultima_atualizacao) {
            element.textContent = `Última atualização: ${this.data.ultima_atualizacao}`;
        }
    }

    /**
     * Atualiza dados forçadamente
     */
    async refreshData() {
        try {
            this.showLoading(true);
            
            // Tenta forçar atualização via endpoint específico
            const response = await fetch(`${this.apiBaseUrl}/api/chamados/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                signal: AbortSignal.timeout(15000)
            });

            if (response.ok) {
                const result = await response.json();
                this.data = result.data;
            } else {
                // Se não conseguir forçar, tenta carregar normalmente
                await this.loadData();
            }

            this.updateDashboard();
            this.hideLoading();
            
        } catch (error) {
            console.error('Erro ao atualizar:', error);
            this.hideLoading();
            this.showError('Erro ao atualizar dados', error.message);
        }
    }

    /**
     * Redimensiona gráficos
     */
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    /**
     * Mostra/oculta loading
     */
    showLoading(show = true) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
    }

    hideLoading() {
        this.showLoading(false);
    }

    /**
     * Mostra erro
     */
    showError(title, message) {
        const errorAlert = document.getElementById('error-alert');
        const errorMessage = document.getElementById('error-message');
        
        if (errorAlert && errorMessage) {
            errorMessage.textContent = message;
            errorAlert.style.display = 'block';
        }
    }

    /**
     * Oculta erro
     */
    hideError() {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.style.display = 'none';
        }
    }

    /**
     * Mostra warning
     */
    showWarning(message) {
        // Cria um alert temporário de warning
        const existingWarning = document.getElementById('warning-alert');
        if (existingWarning) {
            existingWarning.remove();
        }

        const warningDiv = document.createElement('div');
        warningDiv.id = 'warning-alert';
        warningDiv.className = 'alert alert-warning';
        warningDiv.style.cssText = 'background: #fef3c7; border-color: #fbbf24; color: #92400e; margin-bottom: 1.5rem;';
        warningDiv.innerHTML = `
            <div class="alert-content">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <div>
                    <strong>Atenção</strong>
                    <p>${message}</p>
                </div>
            </div>
            <button class="alert-close" onclick="this.parentElement.remove()">×</button>
        `;

        const main = document.querySelector('.main .container');
        if (main) {
            main.insertBefore(warningDiv, main.firstChild);
        }
    }
}

/**
 * Funções globais para modal
 */
function showAbout() {
    const modal = document.getElementById('about-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function showHelp() {
    alert('Para obter ajuda, consulte a documentação no GitHub ou entre em contato com o suporte.');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Fecha modal ao clicar fora
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

// Inicializa o dashboard quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando TechHelp Dashboard...');
    window.dashboard = new TechHelpDashboard();
});

// Adiciona CSS para status badges dinamicamente
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
    }
    .status-aberto { background: #fef3c7; color: #92400e; }
    .status-fechado { background: #d1fae5; color: #065f46; }
    .status-em-andamento { background: #dbeafe; color: #1e40af; }
    .alert-warning { display: block; }
`;
document.head.appendChild(styleSheet);