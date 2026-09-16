Para rodar localmente:

Após clonar o repositório, crie um ambiente virtual e instale as dependências:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copie o arquivo de variáveis de ambiente e ajuste os valores conforme necessário:
```bash
cp .env.example .env  # No Windows: copy .env.example .env
```

Aplique as migrations e crie o primeiro usuário ADMIN (necessário porque `/auth/registrar-interno` já exige um GERENTE/ADMIN logado — sem esse seed não há como criar o primeiro usuário interno pela API):
```bash
alembic upgrade head
python -m scripts.seed_admin
```

Rode a API:
```bash
uvicorn main:app --reload
```