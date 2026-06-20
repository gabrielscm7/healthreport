# PRD: Sistema Inteligente de Relatórios Médicos

**Versão:** 1.0  
**Data:** Jun 2026  
**Status:** Ready for Development  
**Proprietário:** Gabriel Menezes Consultoria  

---

## 1. VISÃO DO PRODUTO

Sistema de IA que automatiza a **organização de exames médicos** e **geração de relatórios estruturados** para apoio à decisão clínica (aptidão cirúrgica). Interface via WhatsApp. Dados sensíveis protegidos por LGPD.

**Tagline:** "Exames organizados. Relatórios inteligentes. Sempre a decisão do médico."

---

## 2. PROBLEMA

| Stakeholder | Problema | Impacto |
|-------------|----------|--------|
| **Clínica** | Organizar exames de pacientes é manual e demorado | 2-4h por paciente |
| **Médico** | Coletar/revisar múltiplos exames leva tempo | Atraso em decisão cirúrgica |
| **Admin** | Sem rastreabilidade de quem acessou dados | Risco LGPD |

---

## 3. SOLUÇÃO

### 3.1 Fluxo Principal

```
Médico/Admin (WhatsApp)
  ↓ "Organize exames de João Silva"
  ↓ Whaha API
  ↓ FastAPI Backend
  ↓ CrewAI Admin Agent (organiza docs, converte MD)
  ↓ LangGraph Specialist (gera relatório)
  ↓ WhatsApp Response
  ↓ Médico recebe relatório estruturado
  ↓ Médico toma decisão (nunca a IA)
```

### 3.2 Funcionalidades Core

#### A. Agente Administrativo
- **Listar documentos** Google Drive/Docs (query: paciente, data)
- **Organizar** em pastas por tipo (exames, imagenologia, laboratorial)
- **Converter** para Markdown (preservando estrutura)
- **Armazenar** em PostgreSQL + S3-compatible
- **Log de acesso** (auditoria)

#### B. Agente Especialista
- **Ler** relatórios em MD (exames + histórico)
- **Estruturar** achados (sem diagnóstico)
- **Gerar relatório** padronizado:
  - Resumo dos exames
  - Achados relevantes (com confiabilidade %)
  - Alertas (resultados fora do esperado)
  - Investigações sugeridas
  - **Disclaimer:** "Ferramenta de apoio. Decisão médica é responsabilidade do médico."
- **Rastreabilidade:** modelo usado, timestamp, versão

#### C. Interface WhatsApp
- **Webhook** Whaha → FastAPI
- **Comandos naturais:**
  - "Organize exames de [paciente]"
  - "Gere relatório para [paciente]"
  - "Ver histórico de [paciente]"
  - "Acesso audit log" (admin only)
- **Resposta imediata** (ACK) + processamento assíncrono

#### D. Auditoria (LGPD/CFM)
- **Audit log imutável:** quem, quando, o quê, resultado
- **Consentimento:** stored para cada paciente
- **Backup:** diário, criptografado, testado
- **Retenção:** 7 anos mínimo

---

## 4. REQUISITOS FUNCIONAIS

### RF1: Organização de Exames
- [x] Conectar Google Workspace
- [x] Buscar docs por paciente
- [x] Converter para MD estruturado
- [x] Validar conteúdo (não quebrado)
- [x] Armazenar com referência original

### RF2: Geração de Relatório
- [x] Ler exames em MD
- [x] Processar com LangGraph
- [x] Adicionar disclaimer obrigatório
- [x] Estruturar em seções (achados, alertas, sugestões)
- [x] Retornar em PDF + JSON

### RF3: Interface WhatsApp
- [x] Receber mensagens via Whaha
- [x] Processar comandos naturais
- [x] Responder em até 5s (ACK)
- [x] Enviar resultado quando pronto
- [x] Suportar 50+ mensagens/dia

### RF4: Controle de Acesso
- [x] RBAC (Admin, Médico, Paciente)
- [x] 2FA para médicos
- [x] Consentimento obrigatório
- [x] Bloqueio por expiração

### RF5: Auditoria
- [x] Log imutável de todas ações
- [x] Rastreamento de acesso (IP, timestamp)
- [x] Relatório de conformidade
- [x] Teste trimestral

---

## 5. REQUISITOS NÃO-FUNCIONAIS

### Segurança
- **Encryption:** AES-256 (repouso) + TLS 1.3 (trânsito)
- **PII:** Nunca em logs, sempre mascarado
- **Validação:** Input sanitization + SQL injection prevention
- **Secrets:** Railway env vars + HashiCorp (futuro)

### Performance
- **Latência:** Webhook response <500ms
- **Processamento:** Relatório em <3min (assíncrono)
- **Throughput:** 100 requisições/min
- **Uptime:** 99.5% (Railway auto-scaling)

### Compliance
- **LGPD:** Art. 1-8, 13, 18-21, 43-49
- **CFM:** Res. 2299/2021 + Parecer 32/2021
- **HIPAA-Brasil:** Backup + retenção + criptografia
- **Audit:** Trail completa, imutável, testada

### Escalabilidade
- **Usuários:** 100 médicos concorrentes
- **Pacientes:** 10k fichas
- **Requisições:** 500k/mês
- **Armazenamento:** 500GB (exames + backups)

---

## 6. PERSONAS

### Persona 1: Médico Cirurgião
- **Tarefa:** Revisar exames antes de aprovar cirurgia
- **Dor:** "Exames espalhados em 5 sistemas diferentes"
- **Sucesso:** Relatório estruturado em 2 min, bem formatado
- **Acesso:** LeRead-only, não pode deletar

### Persona 2: Admin de Clínica
- **Tarefa:** Organizar fichas, garantir completo
- **Dor:** "Paciente X está incompleto, faltam exames"
- **Sucesso:** Dashboard mostrando status de cada paciente
- **Acesso:** Full (criar, editar, deletar), com auditoria

### Persona 3: Paciente
- **Tarefa:** Ver seus próprios exames
- **Dor:** "Não entendo meus resultados"
- **Sucesso:** Visualizar exames + resumo legível
- **Acesso:** View own data only, com consentimento

---

## 7. USER STORIES

### US1: Organizar Exames (Admin)
```
Como admin da clínica
Quero organizar todos os exames de um paciente
Para que o médico tenha tudo centralizado

Critério de Aceitação:
  ✓ Envio mensagem: "Organize exames de João Silva"
  ✓ Sistema busca em Google Drive
  ✓ Converte para MD estruturado
  ✓ Responde: "12 exames organizados. Referência: #ABC123"
  ✓ Audit log registra: quem, quando, resultado
```

### US2: Gerar Relatório (Médico)
```
Como médico cirurgião
Quero gerar relatório para avaliar aptidão
Para decidir se posso operar

Critério de Aceitação:
  ✓ Envio: "Gere relatório para João Silva, ref #ABC123"
  ✓ Sistema processa com Claude Opus
  ✓ Retorna PDF estruturado com:
    - Sumário dos exames
    - Achados relevantes + %confiança
    - Alertas (se houver)
    - Sugestões de investigação
    - Disclaimer obrigatório
  ✓ Tempo: <3 min
```

### US3: Auditoria (Compliance)
```
Como auditor LGPD
Quero acessar log de quem viu dados de qual paciente
Para confirmar conformidade

Critério de Aceitação:
  ✓ Comando: "Audit log para paciente: João Silva"
  ✓ Retorna:
    - Usuário X acessou em 2024-06-17 10:30 UTC
    - IP: 192.168.1.1
    - Ação: VIEW_EXAMS
    - Resultado: success
  ✓ Imutável (nunca deletado)
  ✓ CSV exportável
```

---

## 8. MÉTRICAS DE SUCESSO

| Métrica | Target | Verificação |
|---------|--------|------------|
| **Tempo de resposta** | <500ms webhook ACK | Logs do FastAPI |
| **Taxa de sucesso** | >95% relatórios gerados | DB query |
| **Compliance** | 100% audit trail | Inspeção trimestral |
| **Uptime** | >99.5% | Railway dashboard |
| **Uso** | >50 relatórios/mês | Metrics dashboard |

---

## 9. CONSTRAINTS

### Técnico
- ❌ Sem n8n (Railway Crons + FastAPI)
- ❌ Sem modelo local (DeepSeek não recomendado para saúde)
- ✅ Claude Haiku (admin) + Opus (specialist)
- ✅ PostgreSQL para audit (não NoSQL)

### Legal
- ❌ IA nunca aprova cirurgia (sempre médico)
- ❌ IA nunca comunica paciente diretamente
- ✅ Disclaimer obrigatório em todo relatório
- ✅ Consentimento anterior obrigatório

### Negócio
- Prazo: 4 semanas até MVP
- Budget: $100/mês infra + 200 dev-hours
- Suporte inicial: Gabriel + 1 dev

---

## 10. ROADMAP

### Fase 1 (MVP - Semanas 1-2)
- [x] FastAPI base + PostgreSQL
- [x] Webhook Whaha
- [x] CrewAI admin (listar + organizar docs)
- [x] LangGraph specialist (gerar relatório básico)
- [x] Audit log básico

### Fase 2 (Compliance - Semana 3)
- [x] Encryption AES-256
- [x] RBAC + 2FA
- [x] Consentimento digital
- [x] Backup automático
- [x] Legal review + ajustes

### Fase 3 (Production - Semana 4)
- [x] Testes de carga (100 req/min)
- [x] Penetration test
- [x] Treinamento médicos
- [x] Go-live monitoring

### Fase 4 (Otimização - Post-launch)
- [ ] Dashboard médico (view histórico)
- [ ] Paciente portal (view próprios dados)
- [ ] Comparação exames (antes/depois)
- [ ] Integração com Prontuário Eletrônico

---

## 11. DEPENDÊNCIAS EXTERNAS

| Serviço | Versão | Uso | SLA |
|---------|--------|-----|-----|
| **Whaha API** | v1 | WhatsApp webhook | 99.9% |
| **Google Workspace** | Current | Docs/Drive | 99.99% |
| **OpenAI (Claude)** | Opus 4.6 | Specialist | 99.99% |
| **Railway** | Managed | Infra | 99.95% |
| **PostgreSQL** | 15 | Database | 99.99% |

---

## 12. RISCOS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|--------|-----------|
| Vazamento dados médicos | Baixa | Crítico | Encryption + IP whitelist |
| Relatório com erro | Média | Alto | Disclaimer + médico revisa sempre |
| Compliance LGPD falha | Baixa | Crítico | Legal review + audit trimestral |
| API Whaha down | Baixa | Médio | Fallback SMS (futuro) |
| Cold start Python | Média | Baixo | Railway auto-scaling |

---

## 13. GLOSSÁRIO

- **Audit Log:** Registro imutável de todas ações no sistema
- **LGPD:** Lei Geral de Proteção de Dados (Brasil)
- **CFM:** Conselho Federal de Medicina
- **MD:** Markdown (formato de texto estruturado)
- **RBAC:** Role-Based Access Control
- **PII:** Personally Identifiable Information
- **AES-256:** Encryption padrão militar
- **TLS:** Transport Layer Security (HTTPS)

---

## 14. APROVAÇÃO

| Papel | Nome | Data | Assinatura |
|------|------|------|-----------|
| Product Manager | Gabriel Menezes | Jun 2026 | ✅ |
| Tech Lead | — | — | ⏳ |
| Legal | — | — | ⏳ |
| Médico Responsável | — | — | ⏳ |

---

**Próximo:** Ler `SPEC.md` para detalhes técnicos.
