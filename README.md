# Portfolio System — Fernando Santana

Dashboard de portfolio com preços ao vivo, alertas por email e exportação Excel.

## Arquitetura

| Componente | Tecnologia | Custo |
|---|---|---|
| App / Dashboard | GitHub Pages (HTML+JS) | Grátis |
| Monitor de alertas | GitHub Actions (Python) | Grátis |
| Email de alertas | Gmail SMTP | Grátis |
| Email com Excel | EmailJS | Grátis (200/mês) |
| Preços ao vivo | Yahoo Finance API | Grátis |

---

## Setup — 4 passos

### 1. Criar o repositório no GitHub

```bash
# Clone ou crie um novo repo público chamado "portfolio"
# Habilite GitHub Pages em Settings → Pages → Source: /docs
```

### 2. Configurar secrets no GitHub

Em **Settings → Secrets → Actions**, adicione:

| Secret | Valor |
|---|---|
| `GMAIL_USER` | Seu email Gmail (ex: `fernando@gmail.com`) |
| `GMAIL_APP_PASS` | App Password do Gmail (veja abaixo) |
| `ALERT_EMAIL` | Email para receber alertas (pode ser o mesmo) |

**Como criar Gmail App Password:**
1. Acesse myaccount.google.com → Security
2. Habilite 2-Step Verification
3. App passwords → Create → Mail → nome "portfolio"
4. Copie a senha de 16 caracteres gerada

### 3. Configurar EmailJS (para envio do Excel)

1. Crie conta em [emailjs.com](https://www.emailjs.com/) (grátis)
2. Conecte seu Gmail como serviço
3. Crie um template com variáveis: `{{subject}}`, `{{message}}`, `{{to_email}}`
4. Habilite anexos no template
5. No `docs/index.html`, substitua:
   ```js
   const EMAILJS_SERVICE  = "SUA_SERVICE_ID";
   const EMAILJS_TEMPLATE = "SEU_TEMPLATE_ID";
   const EMAILJS_KEY      = "SUA_PUBLIC_KEY";
   const ALERT_EMAIL      = "seu@email.com";
   ```

### 4. Deploy

```bash
git add .
git commit -m "initial portfolio system"
git push origin main
```

O dashboard estará em: `https://SEU_USUARIO.github.io/portfolio/`

---

## Uso

### App no celular
Acesse `https://SEU_USUARIO.github.io/portfolio/` — os preços atualizam automaticamente ao abrir.

### Alertas automáticos
O monitor roda a cada 15 minutos durante o pregão (9:30–16:00 ET) e envia email quando:
- 🟢 Watchlist ticker entra no **BUY NOW** ou **GOOD** zone
- ✅ Posição aberta atinge o **target de 12 meses**
- 🚨 Posição aberta cruza o **stop loss**

### Excel por email
Clique em "Enviar Excel por email" no app — gera planilha com preços ao vivo e envia para seu Gmail.

---

## Estrutura do repositório

```
portfolio/
├── .github/workflows/
│   └── monitor.yml          # cron a cada 15min
├── docs/
│   └── index.html           # dashboard (GitHub Pages)
├── scripts/
│   └── monitor_prices.py    # lógica de alertas
├── data/
│   ├── state.json           # último signal por ticker
│   └── prices.json          # últimos preços
└── requirements.txt
```

---

## Personalização

Para atualizar targets ou adicionar tickers, edite:
- **`docs/index.html`** → objetos `OPEN` e `WATCH`
- **`scripts/monitor_prices.py`** → dicionários `OPEN` e `WATCH`

Mantê-los sincronizados garante que alertas e dashboard mostram os mesmos dados.
