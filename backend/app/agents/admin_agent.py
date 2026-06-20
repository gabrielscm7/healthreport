# CrewAI Admin Agent — organiza documentos do Google Drive
# Tools: list_google_docs, read_google_doc, convert_to_markdown, upload_to_s3
# Model: Claude Haiku 4.5


def list_google_docs(query: str, limit: int = 20) -> list[dict]:
    """Busca documentos no Google Drive por query de paciente."""
    return []


def read_google_doc(doc_id: str) -> str:
    """Lê o conteúdo de um Google Doc pelo ID."""
    return ""


def convert_to_markdown(content: str) -> str:
    """Converte conteúdo extraído para Markdown estruturado."""
    return content


def upload_to_s3(filename: str, content: str) -> str:
    """Salva conteúdo no S3-compatible (Railway Volumes) e retorna URL."""
    return ""
