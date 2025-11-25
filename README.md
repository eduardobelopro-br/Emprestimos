# 💰 Sistema de Gestão de Empréstimos

Aplicação web para gestão inteligente de dívidas e empréstimos, auxiliando na decisão entre adiantar parcelas ou manter investimentos em CDB.

## 🎯 Funcionalidades

- **Cadastro de Empréstimos**: Registre empréstimos com informações detalhadas (parcelas, taxas, instituição credora)
- **Análise Financeira**: Cálculo automático de descontos e taxa de retorno implícita
- **Comparação com CDB**: Compare o benefício de adiantar vs. investir em CDB a 105% do CDI
- **Recomendações Inteligentes**: Sistema recomenda a melhor estratégia financeira
- **Visualização em Gráficos**: Gráficos interativos mostrando economia potencial
- **Persistência de Dados**: Armazenamento local em SQLite

## 🚀 Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para gerenciamento do banco de dados
- **SQLite**: Banco de dados local leve e eficiente
- **Pydantic**: Validação de dados

### Frontend
- **HTML5/CSS3**: Interface responsiva e moderna
- **JavaScript (Vanilla)**: Lógica do cliente
- **Chart.js**: Visualização de dados em gráficos

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- Navegador web moderno

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/eduardobelopro-br/Emprestimos.git
cd Emprestimos
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Inicie o backend:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

4. Abra o frontend:
   - Navegue até `frontend/index.html` no seu navegador
   - Ou use um servidor HTTP local

## 💡 Como Usar

1. **Cadastrar Empréstimo**:
   - Preencha o formulário com os dados do empréstimo
   - Informe o valor da parcela normal e o valor com desconto para adiantamento
   - Inclua as taxas SELIC e CDI atuais

2. **Visualizar Recomendação**:
   - A tabela mostra todos os empréstimos cadastrados
   - Coluna "Recomendação" indica se deve **Adiantar** ou **Investir**
   - Verde = Adiantar (desconto maior que CDB)
   - Vermelho = Investir (CDB rende mais)

3. **Analisar Economia**:
   - Gráfico mostra economia potencial total por empréstimo
   - Cards superiores exibem economia total e dívida restante

## 🧮 Lógica Financeira

### Cálculo do Desconto Mensal
```
Desconto (%) = (Parcela Normal - Parcela Adiantada) / Parcela Adiantada × 100
```

### Rentabilidade do CDB (105% CDI)
```
Rentabilidade Mensal (%) = (CDI × 1.05) / 12
```

### Recomendação
- **Adiantar**: Se Desconto % > Rentabilidade CDB %
- **Investir**: Se Rentabilidade CDB % > Desconto %

## 📊 Estrutura do Projeto

```
Emprestimos/
├── backend/
│   ├── database.py      # Configuração do banco de dados
│   ├── logic.py         # Lógica financeira
│   └── main.py          # API FastAPI
├── frontend/
│   ├── index.html       # Interface principal
│   ├── styles.css       # Estilos
│   └── app.js           # Lógica do cliente
└── README.md
```

## 🔧 API Endpoints

- `POST /loans` - Criar novo empréstimo
- `GET /loans` - Listar todos os empréstimos
- `GET /dashboard-stats` - Estatísticas do dashboard
- `POST /simulate` - Simular quitação de empréstimo

## 📝 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## 👨‍💻 Autor

Eduardo Belo - [@eduardobelopro-br](https://github.com/eduardobelopro-br)

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.
