# LangGraph Specialist Agent — gera relatórios médicos estruturados
# Nodes: analyze → validate → structure → finalize
# Model: Claude Opus 4.6


MEDICAL_DISCLAIMER = (
    "Este relatório é ferramenta de apoio à decisão clínica. "
    "A decisão final é responsabilidade do médico."
)


def analyze_node(context_md: str) -> dict:
    """Lê exames e identifica achados relevantes com confiança (%)."""
    return {}


def validate_node(analysis: dict) -> dict:
    """Verifica qualidade da análise; se confiança < threshold, refaz."""
    return {}


def structure_node(findings: list) -> dict:
    """Formata relatório: Summary, Findings, Alerts, Recommendations, Disclaimer."""
    return {}


def run_report(context_md: str) -> dict:
    """Executa o grafo completo e retorna relatório estruturado."""
    return {
        "summary": "",
        "findings": [],
        "alerts": [],
        "recommendations": [],
        "disclaimer": MEDICAL_DISCLAIMER,
    }
