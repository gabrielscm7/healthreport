import pytest
from app.agents.specialist_agent import MEDICAL_DISCLAIMER, run_report
from app.agents.admin_agent import list_google_docs, read_google_doc, convert_to_markdown, upload_to_s3


class TestSpecialistAgent:
    def test_disclaimer_present(self):
        result = run_report("")
        assert "ferramenta de apoio" in result["disclaimer"]
        assert "responsabilidade do médico" in result["disclaimer"]

    def test_report_structure(self):
        result = run_report("# Exames de João\nHemoglobina 12.5")
        assert "summary" in result
        assert "findings" in result
        assert "alerts" in result
        assert "recommendations" in result
        assert "disclaimer" in result

    def test_disclaimer_never_empty(self):
        result = run_report("qualquer coisa")
        assert len(result["disclaimer"]) > 0


class TestAdminAgent:
    def test_list_google_docs_returns_list(self):
        result = list_google_docs("João Silva")
        assert isinstance(result, list)

    def test_read_google_doc_returns_string(self):
        result = read_google_doc("doc123")
        assert isinstance(result, str)

    def test_convert_to_markdown_passthrough(self):
        result = convert_to_markdown("# Hello")
        assert result == "# Hello"

    def test_upload_to_s3_returns_string(self):
        result = upload_to_s3("test.md", "# content")
        assert isinstance(result, str)
