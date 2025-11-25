const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    fetchLoans();
    fetchStats();
    setupForm();
});

function setupForm() {
    const form = document.getElementById('loan-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const loanData = {
            name: document.getElementById('name').value,
            creditor: document.getElementById('creditor').value,
            monthly_payment: parseFloat(document.getElementById('monthly_payment').value),
            prepayment_value: parseFloat(document.getElementById('prepayment_value').value),
            total_installments: parseInt(document.getElementById('total_installments').value),
            remaining_installments: parseInt(document.getElementById('remaining_installments').value),
            selic_rate: parseFloat(document.getElementById('selic_rate').value),
            cdi_rate: parseFloat(document.getElementById('cdi_rate').value)
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
            <td>${loan.name}</td>
            <td>${loan.creditor}</td>
            <td>${formatCurrency(loan.monthly_payment)}</td>
            <td>${formatCurrency(loan.prepayment_value)}</td>
            <td>${loan.discount_monthly_percent.toFixed(2)}%</td>
            <td>${loan.cdb_monthly_return.toFixed(2)}%</td>
            <td class="${recClass}">${loan.recommendation}</td>
            <td>${formatCurrency(loan.total_potential_economy)}</td>
        `;
        tbody.appendChild(row);
    });
}

let chartInstance = null;

function renderChart(loans) {
    const ctx = document.getElementById('economyChart').getContext('2d');
    
    const labels = loans.map(l => l.name);
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
