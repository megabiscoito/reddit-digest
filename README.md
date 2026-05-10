# Reddit Digest

Digest diário de subreddits via Claude AI, enviado por email automaticamente.

## Funcionamento

1. Recolhe os posts mais populares dos subreddits configurados via PRAW
2. Gera um resumo inteligente com Claude (temas, tendências, sentimento)
3. Envia um email HTML formatado via Gmail

---

## Setup — Primeira Vez

### 1. Clonar e instalar dependências

```bash
git clone <repo>
cd reddit_digest
pip install -r requirements.txt
```

### 2. Criar app Reddit

1. Aceder a [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Clicar **Create App** → tipo **script**
3. Nome: `reddit_digest` | Redirect URI: `http://localhost:8080`
4. Guardar o **client ID** (texto abaixo do nome da app) e o **client secret**

### 3. Criar App Password no Gmail

1. Aceder a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Requer verificação em dois passos activa
2. Seleccionar **Mail** + **Windows Computer** (ou qualquer dispositivo)
3. Guardar a password gerada (16 caracteres, ex: `abcd efgh ijkl mnop`)

### 4. Obter chave Anthropic

1. Aceder a [console.anthropic.com](https://console.anthropic.com/)
2. API Keys → Create Key

### 5. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Editar `.env` com as credenciais obtidas nos passos anteriores.

### 6. Correr localmente

```bash
python main.py
```

---

## Configuração

| Variável | Descrição | Default |
|---|---|---|
| `SUBREDDITS` | Lista separada por vírgulas | `python,machinelearning,programming` |
| `POSTS_PER_SUBREDDIT` | Posts por subreddit | `10` |
| `TOP_COMMENTS_COUNT` | Comentários por post | `3` |
| `CLAUDE_MODEL` | Modelo Claude a usar | `claude-haiku-4-5` |

**Modelos disponíveis:**
- `claude-haiku-4-5` — rápido e económico, ideal para uso diário (~$0.01/run)
- `claude-opus-4-7` — maior qualidade, mais caro (~$0.30/run)

---

## Automatização com GitHub Actions

### Configurar secrets (credenciais)

No repositório GitHub: **Settings → Secrets and variables → Actions → Secrets**

Adicionar cada secret:

| Secret | Valor |
|---|---|
| `REDDIT_CLIENT_ID` | ID da app Reddit |
| `REDDIT_CLIENT_SECRET` | Secret da app Reddit |
| `REDDIT_USER_AGENT` | ex: `reddit_digest/1.0 by u/username` |
| `ANTHROPIC_API_KEY` | Chave Anthropic |
| `GMAIL_SENDER` | Email Gmail do remetente |
| `GMAIL_APP_PASSWORD` | App Password do Gmail |
| `GMAIL_RECIPIENT` | Email do destinatário |

### Configurar variáveis (configuração não-sensível)

**Settings → Secrets and variables → Actions → Variables**

| Variável | Valor sugerido |
|---|---|
| `SUBREDDITS` | `python,machinelearning,programming` |
| `POSTS_PER_SUBREDDIT` | `10` |
| `TOP_COMMENTS_COUNT` | `3` |
| `CLAUDE_MODEL` | `claude-haiku-4-5` |

### Horário

O workflow corre automaticamente às **8h UTC** (9h Lisboa no inverno, 10h no verão).

Para alterar o horário, editar `.github/workflows/daily_digest.yml`:
```yaml
- cron: '0 8 * * *'  # formato: minuto hora dia mês dia-semana
```

Para correr manualmente: **Actions → Reddit Digest Diário → Run workflow**

---

## Estrutura do Projecto

```
reddit_digest/
├── main.py                          # Ponto de entrada
├── config.py                        # Configuração via .env
├── requirements.txt
├── .env.example                     # Template de configuração
├── modules/
│   ├── reddit_client.py             # PRAW — recolha de posts
│   ├── summarizer.py                # Claude API — geração de resumo
│   └── email_sender.py             # Gmail SMTP — envio de email
├── templates/
│   └── email.html                   # Template HTML do email
└── .github/
    └── workflows/
        └── daily_digest.yml         # GitHub Actions
```
