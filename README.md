# Backend QR Code API

API FastAPI para geração e gerenciamento de QR Codes.

## Estrutura

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Autenticação e autorização
│   ├── config.py        # Configurações
│   ├── database.py      # Configuração do banco de dados
│   ├── main.py          # Aplicação FastAPI
│   ├── models.py        # Modelos SQLModel
│   ├── routes.py        # Rotas da API
│   └── schemas.py       # Schemas Pydantic
├── Dockerfile
├── docker-compose.yml    # Para desenvolvimento local
├── requirements.txt
└── README.md
```

## Desenvolvimento Local

### Com Docker Compose (Recomendado)

```bash
cd backend
docker-compose up -d
```

A API estará disponível em `http://localhost:8001`

### Sem Docker

```bash
# Criar virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DATABASE_URL="sqlite:///./data.db"
export SECRET_KEY="sua-chave-secreta"

# Rodar
uvicorn app.main:app --reload
```

## Variáveis de Ambiente

- `DATABASE_URL`: URL de conexão do banco (default: SQLite)
- `SECRET_KEY`: Chave secreta para JWT (obrigatório em produção)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração do token (default: 43200)
- `AWS_S3_BUCKET`: Nome do bucket S3 (opcional)
- `AWS_ACCESS_KEY_ID`: Access key AWS (opcional)
- `AWS_SECRET_ACCESS_KEY`: Secret key AWS (opcional)
- `AWS_REGION`: Região AWS (default: us-east-2)

## Endpoints

- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Login (OAuth2)
- `GET /me` - Dados do usuário autenticado
- `POST /qrcodes` - Criar QR Code
- `GET /qrcodes` - Listar QR Codes do usuário
- `GET /analytics` - Estatísticas do usuário

Documentação interativa: `http://localhost:8000/docs`

## Deploy

O deploy é feito automaticamente via GitHub Actions quando há push para `main`.

As imagens Docker são publicadas em:
- `ghcr.io/Otto-Schmitz/qcode_backend/backend:latest`
