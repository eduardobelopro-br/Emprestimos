const API_URL = '';

let evolutionChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchLoans();
    fetchStats();
    setupForm();
    setupUpdateModal();
    setupTrackingForm();
    setupFetchRatesTrackingButton();
    setupFetchRatesButton(); // New button for main form
    fetchEvolutionData();
});

function setupFetchRatesButton() {
    const btn = document.getElementById('fetch-rates-btn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = '⏳ Buscando...';

        try {
            const response = await fetch(`${API_URL}/taxas/atuais`);
            const data = await response.json();

            if (response.ok) {
                if (data.selic !== null) {
                    document.getElementById('selic_rate').value = data.selic.toFixed(2);
                }

                if (data.cdi !== null) {
                    document.getElementById('cdi_rate').value = data.cdi.toFixed(2);
                }

                btn.textContent = '✅ Atualizado!';
                // alert('Taxas atualizadas com sucesso!\nSELIC: ' + data.selic + '%\nCDI: ' + data.cdi + '%');
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error('Erro ao buscar taxas');
            }
        } catch (error) {
            console.error('Erro ao buscar taxas do BACEN:', error);
            alert('Erro ao buscar taxas: ' + error.message);
            btn.textContent = '❌ Erro';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.disabled = false;
            }, 3000);
        }
    });
}

function setupForm() {
    const form = document.getElementById('loan-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const loanData = {
            descricao: document.getElementById('name').value,
            instituicao_credora: document.getElementById('creditor').value,
            valor_parcela: parseFloat(document.getElementById('monthly_payment').value),
            valor_parcela_adiantada: parseFloat(document.getElementById('prepayment_value').value),
            qtd_total_parcelas: parseInt(document.getElementById('total_installments').value),
            qtd_parcelas_devidas: parseInt(document.getElementById('remaining_installments').value),
            taxa_selic_registro: parseFloat(document.getElementById('selic_rate').value),
            taxa_cdi_registro: parseFloat(document.getElementById('cdi_rate').value),
            data_cadastro: document.getElementById('start_date').value,
            dia_vencimento: parseInt(document.getElementById('monthly_due_day').value)
        };

        try {
            const response = await fetch(`${API_URL}/loans`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loanData)
            });

            if (response.ok) {
                console.log('Empréstimo cadastrado com sucesso!');
                form.reset();
                await fetchLoans();
                await fetchStats();
            } else {
                console.error('Erro ao cadastrar empréstimo. Status:', response.status);
            }
        } catch (error) {
            console.error('Erro de conexão:', error);
        }
    });
}

function setupUpdateModal() {
    const modal = document.getElementById('update-modal');
    const closeBtn = document.querySelector('.close');
    const updateForm = document.getElementById('update-form');

    if (!modal || !updateForm) return;

    if (closeBtn) {
        closeBtn.onclick = () => {
            modal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };

    updateForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const loanId = document.getElementById('update_loan_id').value;
        const updateData = {
            valor_parcela_adiantada: parseFloat(document.getElementById('update_prepayment_value').value),
            taxa_selic_registro: parseFloat(document.getElementById('update_selic_rate').value),
            taxa_cdi_registro: parseFloat(document.getElementById('update_cdi_rate').value),
            update_date: document.getElementById('update_date').value
        };

        try {
            const response = await fetch(`${API_URL}/loans/${loanId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            if (response.ok) {
                console.log('Empréstimo atualizado com sucesso!');
                modal.style.display = 'none';
                await fetchLoans();
                await fetchStats();
            } else {
                console.error('Erro ao atualizar empréstimo. Status:', response.status);
            }
        } catch (error) {
            console.error('Erro de conexão:', error);
        }
    });
}

function showUpdateModal(loan) {
    const modal = document.getElementById('update-modal');
    if (!modal) return;

    document.getElementById('update_loan_id').value = loan.id;
    document.getElementById('update_loan_name').textContent = loan.descricao;
    document.getElementById('update_prepayment_value').value = loan.valor_parcela_adiantada;
    document.getElementById('update_selic_rate').value = loan.taxa_selic_registro;
    document.getElementById('update_cdi_rate').value = loan.taxa_cdi_registro;

    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('update_date').value = today;

    modal.style.display = 'block';
}

// Monthly Tracking Form Setup
function setupTrackingForm() {
    const form = document.getElementById('tracking-form');
    if (!form) return;

    // Set today as default date
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('tracking_date');
    if (dateInput) dateInput.value = today;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const loanId = document.getElementById('tracking_loan').value;
        const trackingData = {
            data_registro: document.getElementById('tracking_date').value,
            valor_parcela_adiantada: parseFloat(document.getElementById('tracking_value').value),
            taxa_selic: parseFloat(document.getElementById('tracking_selic').value) || null,
            taxa_cdi: parseFloat(document.getElementById('tracking_cdi').value) || null
        };

        try {
            const response = await fetch(`${API_URL}/loans/${loanId}/historico`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(trackingData)
            });

            if (response.ok) {
                console.log('Histórico registrado com sucesso!');
                form.reset();
                if (dateInput) dateInput.value = today;
                await fetchEvolutionData();
                await populateLoanSelect();  // Refresh select
            } else {
                console.error('Erro ao registrar histórico. Status:', response.status);
            }
        } catch (error) {
            console.error('Erro de conexão:', error);
        }
    });
}

function setupFetchRatesTrackingButton() {
    const btn = document.getElementById('fetch-rates-tracking-btn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.textContent = '⏳ Buscando taxas...';

        try {
            const response = await fetch(`${API_URL}/taxas/atuais`);
            const data = await response.json();

            if (response.ok) {
                if (data.selic !== null) {
                    document.getElementById('tracking_selic').value = data.selic.toFixed(2);
                }

                if (data.cdi !== null) {
                    document.getElementById('tracking_cdi').value = data.cdi.toFixed(2);
                }

                btn.textContent = '✅ Taxas atualizadas!';
                setTimeout(() => {
                    btn.textContent = '📊 Buscar Taxas Atuais (BACEN)';
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error('Erro ao buscar taxas');
            }
        } catch (error) {
            console.error('Erro ao buscar taxas do BACEN:', error);
            btn.textContent = '❌ Erro ao buscar';
            setTimeout(() => {
                btn.textContent = '📊 Buscar Taxas Atuais (BACEN)';
                btn.disabled = false;
            }, 3000);
        }
    });
}

async function fetchLoans() {
    try {
        const response = await fetch(`${API_URL}/loans`);
        const loans = await response.json();
        renderTable(loans);
        await populateLoanSelect();
    } catch (error) {
        console.error('Error fetching loans:', error);
    }
}

async function populateLoanSelect() {
    try {
        const response = await fetch(`${API_URL}/loans`);
        const loans = await response.json();
        const select = document.getElementById('tracking_loan');
        if (!select) return;

        // Clear existing options except first one
        select.innerHTML = '<option value="">Selecione um empréstimo</option>';

        loans.forEach(loan => {
            const option = document.createElement('option');
            option.value = loan.id;
            option.textContent = loan.descricao;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error populating loan select:', error);
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${API_URL}/dashboard-stats`);
        const stats = await response.json();

        document.getElementById('total-economy').textContent = formatCurrency(stats.total_potential_economy);
        document.getElementById('total-debt').textContent = formatCurrency(stats.total_outstanding_debt);
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

function renderTable(loans) {
    const tbody = document.querySelector('#loans-table tbody');
    tbody.innerHTML = '';

    loans.forEach(loan => {
        const row = document.createElement('tr');
        const recClass = loan.recommendation === 'Adiantar' ? 'recommendation-adiantar' : 'recommendation-investir';

        row.innerHTML = `
            <td>${loan.descricao}</td>
            <td>${loan.instituicao_credora}</td>
            <td>${formatCurrency(loan.valor_parcela)}</td>
            <td>${formatCurrency(loan.valor_parcela_adiantada)}</td>
            <td>${loan.discount_monthly_percent.toFixed(2)}%</td>
            <td>${loan.cdb_monthly_return.toFixed(2)}%</td>
            <td class="${recClass}">${loan.recommendation}</td>
            <td>${formatCurrency(loan.total_potential_economy)}</td>
            <td><button class="action-btn" onclick='showUpdateModal(${JSON.stringify(loan)})'>Atualizar</button></td>
        `;
        tbody.appendChild(row);
    });
}





// Evolution Chart - Multi-line chart for historical values
async function fetchEvolutionData() {
    try {
        const response = await fetch(`${API_URL}/historico/all`);
        const data = await response.json();
        renderEvolutionChart(data);
    } catch (error) {
        console.error('Error fetching evolution data:', error);
    }
}

function renderEvolutionChart(evolutionData) {
    const ctx = document.getElementById('evolutionChart').getContext('2d');

    if (evolutionChartInstance) {
        evolutionChartInstance.destroy();
    }

    // Generate a unique color for each loan
    const colors = [
        '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
        '#eab308', '#84cc16', '#10b981', '#14b8a6', '#06b6d4'
    ];

    const datasets = evolutionData.map((emprestimo, index) => {
        const color = colors[index % colors.length];
        return {
            label: emprestimo.emprestimo_nome,
            data: emprestimo.historicos.map(h => ({
                x: h.data_registro,
                y: h.valor_parcela_adiantada
            })),
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.3,
            fill: false,
            pointRadius: 5,
            pointHoverRadius: 7
        };
    });

    evolutionChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        displayFormats: {
                            month: 'MMM yyyy'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Data'
                    },
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: 'rgba(51, 65, 85, 0.3)'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Valor Adiantado (R$)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function (value) {
                            return 'R$ ' + value.toFixed(2);
                        }
                    },
                    grid: {
                        color: 'rgba(51, 65, 85, 0.3)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#e2e8f0',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#e2e8f0',
                    bodyColor: '#e2e8f0',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': R$ ' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

// Excel Export/Import Functions
async function exportToExcel() {
    try {
        const response = await fetch(`${API_URL}/export/excel`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'emprestimos_backup.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            console.log('✅ Dados exportados com sucesso!');
            alert('✅ Dados exportados com sucesso!');
        } else {
            throw new Error('Erro ao exportar dados');
        }
    } catch (error) {
        console.error('Erro ao exportar para Excel:', error);
        alert('❌ Erro ao exportar dados para Excel');
    }
}

async function importFromExcel(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/import/excel`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            console.log('✅ Dados importados com sucesso!', result);
            alert(`✅ Dados importados com sucesso!\n\nEmpréstimos: ${result.loans_imported}\nHistórico: ${result.history_imported}`);

            // Recarregar dados
            await fetchLoans();
            await fetchStats();
            await fetchEvolutionData();
        } else {
            throw new Error('Erro ao importar dados');
        }
    } catch (error) {
        console.error('Erro ao importar do Excel:', error);
        alert('❌ Erro ao importar dados do Excel');
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        importFromExcel(file);
        // Limpar o input para permitir selecionar o mesmo arquivo novamente
        event.target.value = '';
    }
}
