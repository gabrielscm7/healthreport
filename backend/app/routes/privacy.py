from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["privacy"])

PRIVACY_POLICY_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Política de Privacidade — Medical Reports</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #1a1a1a; }
        h1 { color: #0d6efd; border-bottom: 2px solid #0d6efd; padding-bottom: 8px; }
        h2 { color: #333; margin-top: 32px; }
        h3 { color: #555; }
        ul { padding-left: 20px; }
        li { margin: 6px 0; }
        .highlight { background: #fff3cd; padding: 12px 16px; border-radius: 6px; border-left: 4px solid #ffc107; }
    </style>
</head>
<body>
    <h1>Política de Privacidade</h1>
    <p><strong>Última atualização:</strong> Junho de 2026</p>
    <p><strong>Controlador:</strong> Gabriel Menezes Consultoria</p>
    <p><strong>DPO (Encarregado):</strong> dpo@medicalreports.app</p>

    <div class="highlight">
        <strong>LGPD — Lei Geral de Proteção de Dados (Lei 13.709/2018)</strong><br>
        Esta política atende aos Artigos 1-8, 13, 18-21, 43-49 da LGPD.
    </div>

    <h2>1. Dados Coletados</h2>
    <h3>1.1 Dados Pessoais</h3>
    <ul>
        <li>Nome completo do paciente (hashed para privacidade)</li>
        <li>CPF (hash SHA-256 com salt — nunca armazenado em texto plano)</li>
        <li>Data de nascimento</li>
        <li>Telefone de contato (WhatsApp)</li>
        <li>Email do profissional de saúde</li>
        <li>Registro CRM (Conselho Regional de Medicina)</li>
    </ul>

    <h3>1.2 Dados Sensíveis (Art. 5, II — LGPD)</h3>
    <ul>
        <li>Exames médicos (criptografados AES-256-GCM)</li>
        <li>Relatórios de análise IA (criptografados)</li>
        <li>Consentimentos assinados digitalmente</li>
        <li>Logs de acesso (auditoria)</li>
    </ul>

    <h2>2. Finalidade do Tratamento (Art. 6 — LGPD)</h2>
    <ul>
        <li>Organização de exames médicos para apoio à decisão clínica</li>
        <li>Geração de relatórios estruturados para avaliação de aptidão cirúrgica</li>
        <li>Auditoria de acesso para conformidade legal (CFM/LGPD)</li>
        <li>Backup e retenção legal (7 anos mínimo)</li>
    </ul>
    <p><strong>Importante:</strong> A IA é ferramenta de apoio. A decisão clínica é SEMPRE do médico responsável.</p>

    <h2>3. Compartilhamento de Dados</h2>
    <ul>
        <li>Dados NÃO são vendidos ou comercializados</li>
        <li>Compartilhamento apenas com profissionais vinculados ao paciente (RBAC)</li>
        <li>Processadores: Railway (infraestrutura), Anthropic (modelo Claude), Google Workspace (documentos fonte)</li>
        <li>Transferência internacional: dados permanecem em servidores com proteção adequada</li>
    </ul>

    <h2>4. Seus Direitos (Art. 18 — LGPD)</h2>
    <ul>
        <li><strong>Acesso:</strong> Solicite todos os seus dados via endpoint <code>GET /lgpd/my-data</code></li>
        <li><strong>Correção:</strong> Solicite correção de dados incompletos via <code>POST /lgpd/correction</code></li>
        <li><strong>Exclusão:</strong> Solicite exclusão (soft delete) via <code>DELETE /lgpd/my-data</code></li>
        <li><strong>Portabilidade:</strong> Exporte seus dados em formato JSON</li>
        <li><strong>Revogação:</strong> Revogue consentimento a qualquer momento via <code>DELETE /consents/{id}</code></li>
        <li><strong>Informação:</strong> Saiba com quem seus dados são compartilhados</li>
    </ul>

    <h2>5. Segurança (Art. 46 — LGPD)</h2>
    <ul>
        <li>Criptografia AES-256-GCM em repouso</li>
        <li>TLS 1.3 em trânsito (HTTPS obrigatório)</li>
        <li>Autenticação 2FA (TOTP) para profissionais de saúde</li>
        <li>RBAC — Controle de acesso baseado em papéis</li>
        <li>Audit log imutável de todas as ações</li>
        <li>Backup diário criptografado</li>
        <li>PII nunca em logs (mascarado)</li>
    </ul>

    <h2>6. Retenção e Descarte</h2>
    <ul>
        <li>Dados retidos por no mínimo 7 anos (exigência CFM/LGPD)</li>
        <li>Soft delete: dados marcados como excluídos, nunca removidos fisicamente</li>
        <li>Backups criptografados com rotação de chaves</li>
        <li>Descarte seguro após período de retenção</li>
    </ul>

    <h2>7. Consentimento (Art. 8 — LGPD)</h2>
    <p>O tratamento de dados sensíveis exige consentimento explícito do titular. O consentimento é:</p>
    <ul>
        <li>Versionado (cada alteração gera nova versão)</li>
        <li>Revogável a qualquer momento</li>
        <li>Registrado com assinatura digital e timestamp</li>
        <li>Vinculado a finalidades específicas</li>
    </ul>

    <h2>8. Incident Response (Art. 48 — LGPD)</h2>
    <p>Em caso de incidente de segurança com dados pessoais:</p>
    <ul>
        <li>Notificação à ANPD em até 72 horas</li>
        <li>Comunicação ao titular dos dados</li>
        <li>Registro completo em audit log imutável</li>
        <li>Plano de resposta documentado</li>
    </ul>

    <h2>9. Contato</h2>
    <p>
        <strong>DPO (Encarregado de Dados):</strong> dpo@medicalreports.app<br>
        <strong>Endereço:</strong> Gabriel Menezes Consultoria<br>
        <strong>ANPD:</strong> <a href="https://www.gov.br/anpd">https://www.gov.br/anpd</a>
    </p>

    <h2>10. Base Legal</h2>
    <ul>
        <li>LGPD — Lei 13.709/2018 (Art. 1-8, 13, 18-21, 43-49)</li>
        <li>CFM — Resolução 2.299/2021 + Parecer 32/2021</li>
        <li>Marco Civil da Internet — Lei 12.965/2014</li>
    </ul>

    <p><em>Esta política é revisada trimestralmente. Última revisão: Junho/2026.</em></p>
</body>
</html>"""


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    return PRIVACY_POLICY_HTML
