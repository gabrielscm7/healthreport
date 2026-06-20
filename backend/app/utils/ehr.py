"""
Connector para Prontuário Eletrônico (EHR).

Suporta:
- HL7 FHIR R4 (padrão internacional)
- Exportação de relatórios em formato FHIR Bundle

Uso:
    from app.utils.ehr import export_report_to_fhir
    bundle = export_report_to_fhir(report_data)
"""
from typing import Optional


def export_report_to_fhir(
    report_id: str,
    patient_name: str,
    doctor_name: str,
    summary: str,
    findings: list[dict],
    generated_at: str,
) -> dict:
    """
    Converte um relatório médico para FHIR Bundle (R4).

    Returns:
        Dict no formato FHIR Bundle que pode ser enviado para EHR.
    """
    entries = []

    diagnostic_report = {
        "fullUrl": f"urn:uuid:{report_id}",
        "resource": {
            "resourceType": "DiagnosticReport",
            "id": report_id,
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report"
                }],
                "text": "Relatório de Apoio à Decisão Clínica"
            },
            "subject": {
                "reference": f"Patient/{patient_name}",
                "display": patient_name
            },
            "performer": [{
                "reference": f"Practitioner/{doctor_name}",
                "display": doctor_name
            }],
            "conclusion": summary,
            "presentedForm": [{
                "contentType": "text/markdown",
                "data": summary,
            }],
            "effectiveDateTime": generated_at,
            "issued": generated_at,
        }
    }
    entries.append(diagnostic_report)

    for idx, finding in enumerate(findings):
        obs = {
            "fullUrl": f"urn:uuid:{report_id}-finding-{idx}",
            "resource": {
                "resourceType": "Observation",
                "id": f"{report_id}-finding-{idx}",
                "status": "final",
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "75323-6",
                        "display": "Finding"
                    }],
                    "text": finding.get("finding", "Achado relevante")
                },
                "subject": {"reference": f"Patient/{patient_name}"},
                "valueString": finding.get("relevance", ""),
                "interpretation": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "CAR",
                        "display": "Critical"
                    }]
                }] if finding.get("confidence", 1.0) < 0.7 else [],
            }
        }
        entries.append(obs)

    return {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": generated_at,
        "entry": entries,
    }


class EHRClient:
    """Cliente abstrato para sistemas EHR externos.

    Para usar:
        client = EHRClient(base_url="https://ehr.clinic.com/fhir")
        client.auth(token="...")
        result = client.send_report(bundle)
    """

    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self._headers: dict[str, str] = {}

    def auth(self, token: str):
        self._headers["Authorization"] = f"Bearer {token}"

    def send_report(self, bundle: dict) -> dict:
        """Envia bundle FHIR para o EHR. Stub — implementar com httpx."""
        return {"status": "simulated", "bundle_size": len(bundle.get("entry", []))}
