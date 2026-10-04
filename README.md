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
