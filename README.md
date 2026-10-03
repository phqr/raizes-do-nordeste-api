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

Aplique as migrations e rode o seed. Ele cria o primeiro usuário ADMIN e os dados de demonstração do Fluxo A: uma unidade, três produtos com estoque, um CLIENTE (`cliente@raizesdonordeste.com`) e um usuário da COZINHA (`cozinha@raizesdonordeste.com`). O ADMIN é `admin@raizesdonordeste.com`, e todos os usuários do seed usam a senha `Demo@1234`. Num banco novo, a unidade e os produtos ficam com IDs a partir de 1:
```bash
alembic upgrade head
python -m scripts.seed
```

Rode a API:
```bash
uvicorn main:app --reload
```