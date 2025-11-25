const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    fetchLoans();
    fetchStats();
    setupForm();
    setupUpdateModal();
});

function setupForm() {
    const form = document.getElementById('loan-form');
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

    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

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

async function fetchLoans() {
    try {
        const response = await fetch(`${API_URL}/loans`);
        const loans = await response.json();
        renderTable(loans);
        renderChart(loans);
    } catch (error) {
        console.error('Error fetching loans:', error);
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

let chartInstance = null;

function renderChart(loans) {
    const ctx = document.getElementById('economyChart').getContext('2d');

    const labels = loans.map(l => l.descricao);
    const data = loans.map(l => l.total_potential_economy);

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Economia Potencial Total (R$)',
                data: data,
                backgroundColor: 'rgba(39, 174, 96, 0.6)',
                borderColor: 'rgba(39, 174, 96, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}
