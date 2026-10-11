# Raízes do Nordeste API

Uma API REST para um sistema de pedidos e fidelidade da rede de lanchonetes nordestinas Raízes do Nordeste. Criada a partir de um estudo de caso da disciplina Projeto Multidisciplinar do CST Analise e Desenvolvimento de Sistemas da UNINTER.

## Requisitos

- **Linguagem:** Python 3.13
- **Framework:** FastAPI + Uvicorn
- **Banco de dados:** SQLite (arquivo `raizes.db`, criado automaticamente)
- **ORM e migrations:** SQLAlchemy + Alembic
- **Principais dependências** (lista completa em `requirements.txt`):
  - `pydantic` - validação
  - `python-jose[cryptography]` - tokens JWT
  - `passlib[bcrypt]` / `bcrypt` - hash de senhas
  - `pytest` - testes

## Para rodar localmente:

### 1. Configurar as variáveis de ambiente

O projeto traz um modelo em `.env.example`. Copie-o para `.env` (que não é versionado) e ajuste os valores:
```bash
cp .env.example .env                # No Windows: copy .env.example .env
```

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` | Não | `sqlite:///./raizes.db` | URL de conexão do SQLAlchemy |
| `JWT_SECRET_KEY` | Sim | - | Chave usada para assinar os tokens JWT. O ideal é um valor longo e aleatório |
| `JWT_ALGORITHM` | Não | `HS256` | Algoritmo de assinatura do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não | `30` | Validade do access token, em minutos |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Não | `7` | Validade do refresh token, em dias |
| `GATEWAY_WEBHOOK_SECRET` | Sim | - | Segredo que o gateway de pagamento envia no header `X-Gateway-Secret` do callback |

Sugestão para gerar uma chave JWT segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Se `JWT_SECRET_KEY` ou `GATEWAY_WEBHOOK_SECRET` estiverem faltando, a aplicação falha ao iniciar.

### 2. Instalar as dependências

Após clonar o repositório, crie um ambiente virtual e instale as dependências:
```bash
python -m venv venv
source venv/bin/activate            # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Criar o banco e executar as migrations

#### Migrations
O banco SQLite é criado automaticamente na primeira migration. Com o ambiente virtual ativo, na raiz do projeto:

```bash
alembic upgrade head
```

#### Seed (dados iniciais)

```bash
python -m scripts.seed
```

O seed cria:

- Usuário **ADMIN**: `admin@raizesdonordeste.com`
- Usuário **CLIENTE**: `cliente@raizesdonordeste.com`
- Usuário da **COZINHA**: `cozinha@raizesdonordeste.com`
- Uma unidade e três produtos com estoque (IDs a partir de 1 num banco novo)

Todos os usuários usam a senha `Demo@1234`.

### 4. Rodar a API

```bash
uvicorn main:app --reload
```

Para conferir se está no ar:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

### 5. Acessar a documentação (Swagger/OpenAPI)

Com a API rodando acesse http://127.0.0.1:8000/docs (Swagger UI)

Para testar endpoints protegidos no Swagger, faça login em `/auth/login` com um dos usuários do seed e use o botão **Authorize** com o token retornado.

Há também uma coleção Postman em `docs/postman/raizes-do-nordeste-api.postman_collection.json`, e os diagramas do projeto ficam em `docs/diagrams/`.

## LGPD e privacidade

### Dados pessoais coletados, finalidade e base legal

| Dado | Obrigatório | Finalidade | Base legal (LGPD, art. 7º) |
|---|---|---|---|
| Nome, e-mail | Sim | Identificar o cliente, autenticar e vincular pedidos | Execução de contrato (V) |
| Senha | Sim | Autenticação (guardada só como hash bcrypt, nunca em texto) | Execução de contrato (V) |
| CPF, data de nascimento | Não | Identificação do cliente e perfil para campanhas | Consentimento (I), dado no cadastro |
| Pedidos, pagamentos | — | Atender o pedido e cumprir obrigações fiscais | Execução de contrato (V) e obrigação legal (II) |
| Pontos e histórico de fidelidade | — | Programa de fidelidade (acúmulo e resgate) | Consentimento específico (I), revogável |

### Como o consentimento é registrado

Os consentimentos ficam na tabela `consentimentos`, com tipo, aceite e data:

- **`CADASTRO_LGPD`**: é obrigatório em `POST /auth/registrar`. Sem `"aceite_lgpd": true`, o cadastro é recusado (400) e nenhum dado é gravado.
- **`FIDELIDADE`**: é opcional e fica em `POST /fidelidade/consentimento`, com `{"aceito": true}` para aceitar ou `false` para revogar. Cada mudança gera um registro novo e vale o mais recente, então o histórico fica preservado. Sem esse consentimento, o cliente não acumula nem resgata pontos.

### Controles de segurança

- As senhas são guardadas com hash bcrypt.
- A autenticação usa JWT, com access token e refresh token. O refresh token fica no banco só como hash SHA-256 e é revogado no logout.
- As permissões dependem do perfil do usuário e a equipe de cada unidade só acessa os dados da própria unidade.
- Os segredos (chave JWT e segredo do webhook de pagamento) ficam no `.env`, que não é versionado.

### Retenção e anonimização (política proposta, não automatizada)

- Os dados cadastrais ficam guardados enquanto a conta estiver ativa.
- Se o titular pedir a exclusão, nome, e-mail, CPF e data de nascimento devem ser anonimizados e a conta desativada. Os pedidos e pagamentos continuam guardados, sem identificar o cliente, pelo prazo exigido pela legislação fiscal.

Nesta versão não há um endpoint para essa anonimização, ela está só documentada.
