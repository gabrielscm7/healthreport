# Plano de Resposta a Incidentes — Medical Reports API

**Versão:** 1.0  
**Última atualização:** Junho 2026  
**Responsável:** Gabriel Menezes Consultoria  
**Contato:** dpo@medicalreports.app

---

## 1. Níveis de Severidade

| Nível | Descrição | SLA Resposta | SLA Resolução |
|-------|-----------|-------------|---------------|
| **P0** | Dados de pacientes vazados ou sistema indisponível | 15 min | 2h |
| **P1** | Funcionalidade crítica quebrada (relatórios, webhook) | 30 min | 4h |
| **P2** | Funcionalidade não crítica quebrada (dashboard, histórico) | 2h | 24h |
| **P3** | Bug cosmético, melhoria solicitada | 24h | 7 dias |

---

## 2. Runbook de Resposta

### 2.1 P0 — Vazamento de Dados ou Sistema Indisponível

```
1. DETECTAR
   ├─ Sentry alerta de erro rate > 5%
   ├─ Railway alerta de CPU > 80% / mem > 85%
   └─ Médico reporta sistema fora do ar via WhatsApp

2. TRIAGEM (15 min)
   ├─ Verificar Railway dashboard
   ├─ Verificar logs: railway logs -s fastapi
   ├─ Verificar banco: psql $DATABASE_URL -c "SELECT count(*) FROM audit_logs"
   └─ Verificar Redis: redis-cli -u $REDIS_URL PING

3. CONTER (30 min)
   ├─ Se vazamento: rotacionar todas as chaves (ENCRYPTION_KEY, SECRET_KEY)
   ├─ Se indisponibilidade: aumentar réplicas (railway scale --replicas 5)
   ├─ Se banco corrompido: restaurar backup
   └─ Bloquear IP suspeito se detectado

4. NOTIFICAR (72h — LGPD Art. 48)
   ├─ Comunicar ANPD (gov.br/anpd)
   ├─ Notificar titulares afetados
   └─ Registrar em audit log imutável

5. RECUPERAR (2h)
   ├─ Restaurar último backup íntegro
   ├─ Verificar integridade dos dados
   ├─ Testar health checks
   ├─ Validar consentimentos ainda válidos
   └─ Liberar acesso gradualmente

6. PÓS-MORTEM (24h)
   ├─ Documentar causa raiz
   ├─ Implementar correção preventiva
   └─ Atualizar runbook
```

### 2.2 P1 — Funcionalidade Crítica Quebrada

```
1. IDENTIFICAR
   ├─ Sentry alerta de erro
   ├─ Usuário reporta no WhatsApp
   └─ Verificar logs recentes

2. DIAGNOSTICAR
   ├─ Testar endpoints manualmente:
     ├─ curl https://api.medicalreports.app/health
     ├─ curl https://api.medicalreports.app/health/db
     └─ curl https://api.medicalreports.app/health/cache
   ├─ Verificar última release (git log --oneline -5)
   └─ Verificar dependências externas (Whaha, Claude, Google)

3. CORRIGIR
   ├─ Rollback para última versão estável se necessário
   ├─ Deploy de hotfix via GitHub (push em branch fix/)
   └─ Verificar Railway deploy logs

4. VERIFICAR
   ├─ Testes passando: pytest tests/ -v
   ├─ Health checks ok
   └─ Mensagem de confirmação ao usuário
```

---

## 3. Contatos de Emergência

| Papel | Nome | Contato |
|-------|------|---------|
| Tech Lead | Tech Lead | tech-lead@medicalreports.app |
| DPO/LGPD | DPO | dpo@medicalreports.app |
| Whaha API | Suporte | support@whaha.com |
| Anthropic/Claude | Suporte | support@anthropic.com |
| Railway | Infra | support@railway.app |

---

## 4. Backup & Restore

### Backup Diário
```bash
# Automático (Railway Cron)
python scripts/backup.py

# Manual
pg_dump -F c $DATABASE_URL > /data/backups/manual_$(date +%Y%m%d).dump
```

### Restore
```bash
# Restaurar backup criptografado
openssl enc -d -aes-256-cbc -in backup.sql.enc -out backup.sql -pass pass:$KEY

# Restaurar no banco
psql $DATABASE_URL < backup.sql

# Verificar integridade
python -c "
import hashlib
s = open('backup.sql', 'rb').read()
print(hashlib.sha256(s).hexdigest())
# Comparar com checksum salvo
"
```

### Teste Trimestral
- Restaurar backup em ambiente de staging
- Rodar test suite completo
- Verificar audit logs íntegros
- Gerar relatório de conformidade

---

## 5. Comunicação

### Template de Notificação LGPD (Art. 48)

```
Assunto: [URGENTE] Notificação de Incidente de Segurança — Medical Reports

Prezado(a),

Informamos que em [DATA] às [HORA] foi identificado um incidente de
segurança envolvendo dados pessoais tratados pelo sistema Medical Reports.

Natureza do Incidente: [descrição]
Dados Afetados: [tipos de dados]
Titulares Afetados: [quantidade ou "indeterminado"]
Medidas Tomadas: [ações de contenção]
Contato DPO: dpo@medicalreports.app

Este comunicado atende ao Art. 48 da Lei 13.709/2018 (LGPD).
```

---

## 6. Revisão

| Data | Responsável | Alterações |
|------|-------------|------------|
| Jun 2026 | Tech Lead | Criação inicial do plano |
| Trimestral | DPO | Revisão e atualização |
