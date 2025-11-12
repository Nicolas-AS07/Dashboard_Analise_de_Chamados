/* ====================================
   TechHelp Dashboard v2.0 - JavaScript
   Professional Analytics Dashboard
   ======================================== */

class TechHelpDashboard {
    constructor() {
        // Detecta automaticamente se está em produção ou desenvolvimento
        const isProduction = window.location.hostname !== 'localhost' && 
                           window.location.hostname !== '127.0.0.1';
        
        this.apiUrl = isProduction 
            ? '/api'  // Em produção, usa o mesmo domínio
            : 'http://localhost:5001/api';  // Em desenvolvimento, porta 5001
        
        console.log('🌐 Ambiente:', isProduction ? 'Produção' : 'Desenvolvimento');
        console.log('🔗 API URL:', this.apiUrl);
        
        this.data = null;
        this.charts = {};
        this.filters = {
            tecnicoPeriod: 'all',
            categoriaType: 'doughnut'  // Chart.js v4 usa 'doughnut' não 'donut'
        };
        
        this.init();
    }

    async init() {
        console.log('Inicializando TechHelp Dashboard v2.0...');
        // Aplicar tema (padrão: dark)
        this.applyTheme();
        
        // Event Listeners
        this.setupEventListeners();
        
        // Carregar dados iniciais
        await this.loadData();
        
        // Auto-refresh a cada 5 minutos
        setInterval(() => this.loadData(true), 5 * 60 * 1000);
    }

    // ===== Tema e Utilidades =====
    getCssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    isDarkTheme() {
        return (document.documentElement.getAttribute('data-theme') || 'dark') === 'dark';
    }

    applyTheme(theme) {
        const existing = document.documentElement.getAttribute('data-theme');
        const active = theme || existing || localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', active);
        
        // Ajustes globais do Chart.js baseados nas variáveis CSS
        // IMPORTANTE: Estes defaults NÃO devem afetar backgroundColor dos datasets
        const tickColor = this.getCssVar('--text-secondary') || '#8b949e';
        const gridColor = this.getCssVar('--border-light') || 'rgba(48, 54, 61, 0.3)';
        
        // Apenas configurar cores de texto e bordas globais, NÃO backgroundColor
        Chart.defaults.color = tickColor;
        Chart.defaults.borderColor = gridColor;
        
        console.log('🎨 Chart.js defaults aplicados:', {
            textColor: tickColor,
            borderColor: gridColor
        });
        
        // Atualizar botão
        const labelTheme = document.getElementById('label-theme');
        const iconTheme = document.getElementById('icon-theme');
        if (labelTheme && iconTheme) {
            if (active === 'dark') {
                labelTheme.textContent = 'Escuro';
                iconTheme.innerHTML = `\n                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>\n                    </svg>\n                `;
            } else {
                labelTheme.textContent = 'Claro';
                iconTheme.innerHTML = `\n                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">\n                        <circle cx="12" cy="12" r="5"></circle>\n                        <path d="M12 1v2m0 18v2m11-11h-2M3 12H1m16.95 7.05-1.41-1.41M6.46 6.46 5.05 5.05m12.9 0-1.41 1.41M6.46 17.54 5.05 18.95"></path>\n                    </svg>\n                `;
            }
        }
    }

    setupEventListeners() {
        // Botão de refresh
        const btnRefresh = document.getElementById('btn-refresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.refreshData());
        }
        
        // Botão de tema (opcional - não existe no HTML atual)
        const btnTheme = document.getElementById('btn-theme-toggle');
        if (btnTheme) {
            btnTheme.addEventListener('click', () => this.toggleTheme());
        }

        // Filtros
        const filterTecnico = document.getElementById('filter-tecnico-period');
        if (filterTecnico) {
            filterTecnico.addEventListener('change', (e) => {
                this.filters.tecnicoPeriod = e.target.value;
                this.updateChartTecnico();
            });
        }

        const filterCategoria = document.getElementById('filter-categoria-type');
        if (filterCategoria) {
            filterCategoria.addEventListener('change', (e) => {
                this.filters.categoriaType = e.target.value;
                this.updateChartCategoria();
            });
        }
    }

    async loadData(silent = false) {
        try {
            if (!silent) this.showLoading();
            
            console.log('Carregando dados da API...');
            
            const response = await fetch(`${this.apiUrl}/chamados`);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
            }
            
            this.data = await response.json();
            
            console.log('Dados carregados:', this.data);
            
            // Atualizar UI
            this.updateKPIs();
            this.createCharts();
            this.updateLastUpdate();
            this.hideError();
            
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            this.showError(`Erro ao carregar dados: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    // ========= Helpers de formatação =========
    formatNumber(value) {
        try { return Number(value || 0).toLocaleString('pt-BR'); } catch { return String(value); }
    }

    formatPercent(value, digits = 1) {
        const num = Number(value || 0);
        return num.toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }) + '%';
    }

    async refreshData() {
        const btn = document.getElementById('btn-refresh');
        if (btn) {
            btn.classList.add('loading');
            btn.disabled = true;
        }
        
        await this.loadData();
        
        if (btn) {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    updateKPIs() {
        if (!this.data) return;

        // Adaptar para o formato da API atual
        const kpis = {
            total_chamados: this.data.total_chamados || 0,
            chamados_abertos: this.data.total_abertos || 0,
            chamados_fechados: this.data.total_fechados || 0,
            tempo_medio_atendimento: parseFloat(this.data.tempo_medio_resolucao) || 0
        };

        // Total de Chamados
        this.animateNumber('kpi-total', kpis.total_chamados);
        
        // Chamados Abertos
        this.animateNumber('kpi-abertos', kpis.chamados_abertos);
        
        // Chamados Fechados
        this.animateNumber('kpi-fechados', kpis.chamados_fechados);
        
        // TMA (Tempo Médio de Atendimento)
        this.animateNumber('kpi-tma', kpis.tempo_medio_atendimento, 1);

        // Atualizar trends (calcular baseado em comparações)
        this.updateTrends(kpis);

        // Atualizar comparações
        this.updateComparisons(kpis);
    }

    updateTrends(kpis) {
        // Simular trends (em produção, viria do backend)
        const trends = {
            total: this.calculateTrend(kpis.total_chamados, 500),
            abertos: this.calculateTrend(kpis.chamados_abertos, 300),
            fechados: this.calculateTrend(kpis.chamados_fechados, 180),
            tma: this.calculateTrend(kpis.tempo_medio_atendimento, 15, true) // invertido
        };

        this.updateTrendElement('trend-total', trends.total);
        this.updateTrendElement('trend-abertos', trends.abertos);
        this.updateTrendElement('trend-fechados', trends.fechados);
        this.updateTrendElement('trend-tma', trends.tma);
    }

    calculateTrend(current, previous, inverted = false) {
        const diff = current - previous;
        const percentage = previous > 0 ? ((diff / previous) * 100).toFixed(1) : 0;
        const isPositive = inverted ? diff < 0 : diff > 0;
        
        return {
            value: Math.abs(percentage),
            isPositive,
            symbol: isPositive ? '↗' : '↘'
        };
    }

    updateTrendElement(elementId, trend) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.className = `kpi-trend ${trend.isPositive ? 'up' : 'down'}`;
        element.innerHTML = `
            <span>${trend.symbol}</span>
            <span>${trend.value > 0 ? '+' : ''}${trend.value}%</span>
        `;
    }

    updateComparisons(kpis) {
        // Total no mês atual (simplificado)
        const totalMesAtual = document.getElementById('total-mes-atual');
        if (totalMesAtual) {
            totalMesAtual.textContent = Math.round(kpis.total_chamados * 0.3);
        }
    }

    animateNumber(elementId, targetValue, decimals = 0) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const duration = 1000; // 1 segundo
        const startValue = parseFloat(element.textContent.replace(/[^0-9.]/g, '')) || 0;
        const startTime = Date.now();

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            
            const currentValue = startValue + (targetValue - startValue) * easeOut;
            element.textContent = currentValue.toFixed(decimals);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetValue.toFixed(decimals);
            }
        };

        requestAnimationFrame(animate);
    }

    createCharts() {
        if (!this.data) return;

        // Destruir gráficos existentes
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};

        // Criar novos gráficos
        this.createChartTecnico();
        this.createChartCategoria();
        this.createChartStatus();
        this.createChartSatisfacao();
    }

    createChartTecnico() {
        const ctx = document.getElementById('chart-tecnico');
        if (!ctx || !this.data.chamados_por_tecnico) return;

        // Converter objeto para array e ordenar
        const data = this.data.chamados_por_tecnico;
        const sorted = Object.entries(data)
            .map(([label, value]) => ({ label, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10);

        const labels = sorted.map(item => item.label);
        const valores = sorted.map(item => item.value);

        // Paleta de cores profissional
        const colors = this.generateColorPalette(labels.length, 'blue');

        const tickColor = this.getCssVar('--text-secondary') || '#cbd5e1';
        const labelColor = this.getCssVar('--text-primary') || '#f1f5f9';
        const gridColor = this.isDarkTheme() ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.05)';
        const tooltipBg = this.isDarkTheme() ? 'rgba(17, 21, 31, 0.97)' : 'rgba(0, 0, 0, 0.8)';
        const tooltipBorder = this.isDarkTheme() ? 'rgba(148, 163, 184, 0.2)' : 'rgba(255, 255, 255, 0.2)';

        this.charts.tecnico = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Chamados',
                    data: valores,
                    backgroundColor: colors.background,
                    borderColor: colors.border,
                    borderWidth: 2,
                    borderRadius: 8,
                    hoverBackgroundColor: colors.hover
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // Barras horizontais
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        padding: 12,
                        titleFont: { size: 14, weight: '600' },
                        bodyFont: { size: 13 },
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const total = valores.reduce((a, b) => a + b, 0);
                                const percentage = (context.parsed.x / total) * 100;
                                return `${this.formatNumber(context.parsed.x)} chamados (${this.formatPercent(percentage)})`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: gridColor
                        },
                        ticks: {
                            font: { size: 12 },
                            color: tickColor
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: { size: 12, weight: '500' },
                            color: labelColor
                        }
                    }
                }
            }
        });

        // Gerar insight
        this.generateInsightTecnico(sorted);
    }

    createChartCategoria() {
        const ctx = document.getElementById('chart-categoria');
        if (!ctx || !this.data.categorias) return;

        // Destruir gráfico anterior se existir
        if (this.charts.categoria) {
            try {
                this.charts.categoria.destroy();
                this.charts.categoria = null;
            } catch (e) {
                console.warn('Erro ao destruir gráfico categoria:', e);
            }
        }

        // Converter objeto para array e ordenar
        const data = this.data.categorias;
        const sorted = Object.entries(data)
            .map(([label, value]) => ({ label, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 8);

        const labels = sorted.map(item => item.label);
        const valores = sorted.map(item => item.value);

        const colors = this.generateColorPalette(labels.length, 'rainbow');

        const chartType = this.filters.categoriaType || 'doughnut';

        const tickColor = this.getCssVar('--text-secondary') || '#cbd5e1';
        const labelColor = this.getCssVar('--text-primary') || '#f1f5f9';
        const gridColor = this.isDarkTheme() ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.05)';
        const tooltipBg = this.isDarkTheme() ? 'rgba(17, 21, 31, 0.97)' : 'rgba(0, 0, 0, 0.8)';
        const tooltipBorder = this.isDarkTheme() ? 'rgba(148, 163, 184, 0.2)' : 'rgba(255, 255, 255, 0.2)';

        this.charts.categoria = new Chart(ctx, {
            type: chartType,  // Usar diretamente o tipo (já é 'doughnut' ou 'bar')
            data: {
                labels: labels,
                datasets: [{
                    label: 'Ocorrências',
                    data: valores,
                    backgroundColor: colors.background,
                    borderColor: this.isDarkTheme() ? '#11151f' : '#ffffff',
                    borderWidth: 3,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: { size: 12, weight: '500' },
                            color: labelColor,
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        padding: 12,
                        titleFont: { size: 14, weight: '600' },
                        bodyFont: { size: 13 },
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const total = valores.reduce((a, b) => a + b, 0);
                                const percentage = (context.parsed / total) * 100;
                                return `${this.formatNumber(context.parsed)} ocorrências (${this.formatPercent(percentage)})`;
                            }
                        }
                    }
                },
                ...(chartType === 'bar' && {
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: gridColor },
                            ticks: {
                                font: { size: 12 },
                                color: tickColor
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 12, weight: '500' },
                                color: labelColor
                            }
                        }
                    }
                })
            }
        });

        // Gerar insight
        this.generateInsightCategoria(sorted);
    }

    createChartStatus() {
        const ctx = document.getElementById('chart-status');
        if (!ctx) return;

        // Destruir gráfico anterior se existir
        if (this.charts.status) {
            try {
                this.charts.status.destroy();
                this.charts.status = null;
            } catch (e) {
                console.warn('Erro ao destruir gráfico status:', e);
            }
        }

        // Criar gráfico de status baseado nos dados disponíveis
        const abertos = this.data.total_abertos || 0;
        const fechados = this.data.total_fechados || 0;

        const labels = ['Abertos', 'Fechados'];
        const valores = [abertos, fechados];

        // Cores diretas - não usar objeto de mapeamento
        const backgrounds = [
            '#f59e0b',    // Abertos - Amarelo âmbar vibrante (SEM transparência)
            '#10b981'     // Fechados - Verde esmeralda (SEM transparência)
        ];
        
        const borders = [
            '#f59e0b',  // Amarelo âmbar
            '#10b981'   // Verde esmeralda
        ];
        
        const hovers = [
            '#fbbf24',       // Amarelo mais claro
            '#34d399'        // Verde mais claro
        ];

        console.log('🎨 Criando gráfico de Status com cores:', {
            backgrounds,
            borders,
            hovers,
            labels,
            valores
        });

        const labelColor = this.getCssVar('--text-primary') || '#e6edf3';
        const tooltipBg = 'rgba(13, 17, 23, 0.95)';
        const tooltipBorder = 'rgba(48, 54, 61, 0.8)';

        this.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: valores,
                    backgroundColor: backgrounds,
                    borderColor: '#0d1117',
                    borderWidth: 3,
                    hoverBackgroundColor: hovers,
                    hoverBorderColor: borders,
                    hoverBorderWidth: 4,
                    hoverOffset: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { size: 13, weight: '500', family: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' },
                            color: labelColor,
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            generateLabels: (chart) => {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: label,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    strokeStyle: data.datasets[0].borderColor,
                                    lineWidth: data.datasets[0].borderWidth,
                                    hidden: false,
                                    index: i
                                }));
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        padding: 12,
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const total = valores.reduce((a, b) => a + b, 0);
                                const percentage = (context.parsed / total) * 100;
                                return `${context.label}: ${this.formatNumber(context.parsed)} (${this.formatPercent(percentage)})`;
                            }
                        }
                    }
                }
            }
        });

        // Gerar insight
        const dataForInsight = { labels, valores };
        this.generateInsightStatus(dataForInsight);
    }

    createChartSatisfacao() {
        const ctx = document.getElementById('chart-satisfacao');
        if (!ctx) return;

        // Dados de satisfação fictícios (pois a API atual não retorna)
        // Você pode adicionar isso no backend depois
        const labels = ['1 ⭐', '2 ⭐', '3 ⭐', '4 ⭐', '5 ⭐'];
        const valores = [10, 20, 150, 200, 170]; // Simulado

        // Teoria das cores: Escala de calor emocional (vermelho = negativo, verde = positivo)
        const colors = {
            '1 ⭐': { 
                bg: 'rgba(239, 68, 68, 0.8)',      // Vermelho - Muito insatisfeito
                border: '#ef4444',
                hover: 'rgba(239, 68, 68, 1)'
            },
            '2 ⭐': { 
                bg: 'rgba(249, 115, 22, 0.8)',     // Laranja - Insatisfeito
                border: '#f97316',
                hover: 'rgba(249, 115, 22, 1)'
            },
            '3 ⭐': { 
                bg: 'rgba(251, 191, 36, 0.8)',     // Amarelo - Neutro
                border: '#fbbf24',
                hover: 'rgba(251, 191, 36, 1)'
            },
            '4 ⭐': { 
                bg: 'rgba(132, 204, 22, 0.8)',     // Verde lima - Satisfeito
                border: '#84cc16',
                hover: 'rgba(132, 204, 22, 1)'
            },
            '5 ⭐': { 
                bg: 'rgba(16, 185, 129, 0.8)',     // Verde esmeralda - Muito satisfeito
                border: '#10b981',
                hover: 'rgba(16, 185, 129, 1)'
            }
        };

        const backgrounds = labels.map(label => colors[label]?.bg || '#94a3b8');
        const borders = labels.map(label => colors[label]?.border || '#64748b');
        const hovers = labels.map(label => colors[label]?.hover || '#cbd5e1');

        const tickColor = this.getCssVar('--text-secondary') || '#8b949e';
        const labelColor = this.getCssVar('--text-primary') || '#e6edf3';
        const gridColor = 'rgba(48, 54, 61, 0.3)';
        const tooltipBg = 'rgba(13, 17, 23, 0.95)';
        const tooltipBorder = 'rgba(48, 54, 61, 0.8)';

        this.charts.satisfacao = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Avaliações',
                    data: valores,
                    backgroundColor: backgrounds,
                    borderColor: borders,
                    borderWidth: 2,
                    borderRadius: 8,
                    hoverBackgroundColor: hovers,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: tooltipBg,
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        padding: 12,
                        borderColor: tooltipBorder,
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => {
                                const total = valores.reduce((a, b) => a + b, 0);
                                const percentage = (context.parsed.y / total) * 100;
                                return `${this.formatNumber(context.parsed.y)} avaliações (${this.formatPercent(percentage)})`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: gridColor },
                        ticks: {
                            font: { size: 12 },
                            color: tickColor
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { size: 13, weight: '500' },
                            color: labelColor
                        }
                    }
                }
            }
        });

        // Gerar insight
        const dataForInsight = { labels, valores };
        this.generateInsightSatisfacao(dataForInsight);
    }

    updateChartTecnico() {
        if (this.charts.tecnico) {
            this.charts.tecnico.destroy();
        }
        this.createChartTecnico();
    }

    updateChartCategoria() {
        // Destruir gráfico existente de forma mais agressiva
        if (this.charts.categoria) {
            try {
                this.charts.categoria.destroy();
                this.charts.categoria = null;
            } catch (e) {
                console.warn('Erro ao destruir gráfico:', e);
            }
        }
        
        // Limpar o canvas manualmente
        const canvas = document.getElementById('chart-categoria');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        
        // Pequeno delay para garantir limpeza
        setTimeout(() => {
            this.createChartCategoria();
        }, 50);
    }

    generateColorPalette(count, type = 'blue') {
        // Teoria das cores para dashboards - Paleta otimizada para acessibilidade
        const palettes = {
            blue: [
                '#60a5fa', // Azul claro
                '#3b82f6', // Azul
                '#2563eb', // Azul médio
                '#1d4ed8', // Azul escuro
                '#1e40af'  // Azul profundo
            ],
            rainbow: [
                '#60a5fa', // Azul - Primário/Neutro
                '#a78bfa', // Roxo - Criatividade
                '#ec4899', // Rosa - Destaque
                '#f97316', // Laranja - Energia
                '#fbbf24', // Amarelo - Atenção
                '#34d399', // Verde - Sucesso
                '#06b6d4', // Ciano - Info
                '#8b5cf6'  // Violeta - Especial
            ]
        };

        const baseColors = palettes[type] || palettes.blue;
        const colors = [];

        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }

        return {
            background: colors.map(c => c + 'CC'), // 80% opacity
            border: colors,
            hover: colors.map(c => c + 'FF') // 100% opacity
        };
    }

    generateInsightTecnico(data) {
        const element = document.getElementById('insight-tecnico');
        if (!element || !data.length) return;

        const topTecnico = data[0];
        const total = data.reduce((sum, item) => sum + item.value, 0);
        const percentage = (topTecnico.value / total) * 100;

        element.innerHTML = `
            <strong>${topTecnico.label}</strong> lidera o volume com 
            <strong>${this.formatNumber(topTecnico.value)} chamados</strong> 
            (${this.formatPercent(percentage)} do total).
        `;
    }

    generateInsightCategoria(data) {
        const element = document.getElementById('insight-categoria');
        if (!element || !data.length) return;

        const topCategoria = data[0];
        const total = data.reduce((sum, item) => sum + item.value, 0);
        const percentage = (topCategoria.value / total) * 100;

        element.innerHTML = `
            <strong>${topCategoria.label}</strong> concentra 
            <strong>${this.formatPercent(percentage)}</strong> dos chamados 
            (<strong>${this.formatNumber(topCategoria.value)}</strong> ocorrências).
        `;
    }

    generateInsightStatus(data) {
        const element = document.getElementById('insight-status');
        if (!element) return;

    const total = data.valores.reduce((a, b) => a + b, 0);
    const abertoIndex = data.labels.findIndex(l => ['Aberto','Abertos','Pendente'].includes(l));
    const fechadoIndex = data.labels.findIndex(l => ['Fechado','Fechados','Resolvido','Resolvidos'].includes(l));

        const abertos = abertoIndex >= 0 ? data.valores[abertoIndex] : 0;
        const fechados = fechadoIndex >= 0 ? data.valores[fechadoIndex] : 0;
        const taxaResolucao = ((fechados / total) * 100).toFixed(1);

        element.innerHTML = `
            Taxa de resolução: <strong>${this.formatPercent(taxaResolucao)}</strong>. 
            <strong>${this.formatNumber(abertos)} chamados</strong> em aberto.
        `;
    }

    generateInsightSatisfacao(data) {
        const element = document.getElementById('insight-satisfacao');
        if (!element) return;

    const total = data.valores.reduce((a, b) => a + b, 0);
        const positivos = data.valores.slice(-2).reduce((a, b) => a + b, 0); // 4 e 5 estrelas
    const taxaPositiva = (positivos / total) * 100;

        const media = data.labels.reduce((sum, label, i) => {
            return sum + (parseInt(label) * data.valores[i]);
        }, 0) / total;

        element.innerHTML = `
            Satisfação média: <strong>${media.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong>. 
            <strong>${this.formatPercent(taxaPositiva)}</strong> das avaliações são positivas (4-5 estrelas).
        `;
    }

    updateLastUpdate() {
        const element = document.getElementById('last-update-text');
        if (!element) return;

        const now = new Date();
        const formatted = now.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        element.textContent = `Última atualização: ${formatted}`;
    }

    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showError(message) {
        const alert = document.getElementById('error-alert');
        const text = document.getElementById('error-text');
        
        if (alert && text) {
            text.textContent = message;
            alert.style.display = 'block';
            
            // Auto-hide após 10 segundos
            setTimeout(() => this.hideError(), 10000);
        }
    }

    hideError() {
        const alert = document.getElementById('error-alert');
        if (alert) {
            alert.style.display = 'none';
        }
    }

    toggleTheme() {
        console.log('toggleTheme() chamado!');
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        console.log('Tema atual:', current);
        const next = current === 'dark' ? 'light' : 'dark';
        console.log('Próximo tema:', next);
        localStorage.setItem('theme', next);
        this.applyTheme(next);
        if (this.data) {
            console.log('Recriando gráficos...');
            this.createCharts();
        }
        console.log('Tema alterado com sucesso!');
    }
}

// Inicializar quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new TechHelpDashboard();
    });
} else {
    new TechHelpDashboard();
}
