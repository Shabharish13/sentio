from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.config import get_settings

# HubSpot-defined default association type IDs
ASSOC_DEAL_TO_CONTACT = 3
ASSOC_NOTE_TO_DEAL = 214


class HubSpotClient:
    """HubSpot CRM v3: contact/deal upsert and note attachment.

    Idempotent by email/name so repeat bookings refresh records instead of
    duplicating them. Stage is set by the caller's routing outcome.
    """

    BASE = "https://api.hubapi.com"

    def __init__(self, http: httpx.Client | None = None) -> None:
        s = get_settings()
        self._token = s.hubspot_token
        self._pipeline = s.hubspot_pipeline_id
        self._http = http or httpx.Client(timeout=30)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def upsert_contact(self, email: str, properties: dict) -> str:
        body = {
            "inputs": [
                {
                    "idProperty": "email",
                    "id": email,
                    "properties": {"email": email, **properties},
                }
            ]
        }
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/contacts/batch/upsert",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["results"][0]["id"]

    def _find_deal_id(self, name: str) -> str | None:
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/deals/search",
            headers=self._headers(),
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {"propertyName": "dealname", "operator": "EQ", "value": name}
                        ]
                    }
                ]
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0]["id"] if results else None

    def upsert_deal(self, name: str, stage: str, contact_id: str,
                    priority: str | None = None, amount: float | None = None) -> str:
        props: dict = {"dealstage": stage, "pipeline": self._pipeline}
        if priority:
            props["priority"] = priority
        if amount is not None:
            props["amount"] = str(int(float(amount)))

        existing = self._find_deal_id(name)
        if existing:
            resp = self._http.patch(
                f"{self.BASE}/crm/v3/objects/deals/{existing}",
                headers=self._headers(),
                json={"properties": props},
            )
            resp.raise_for_status()
            return existing

        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/deals",
            headers=self._headers(),
            json={
                "properties": {"dealname": name, **props},
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": ASSOC_DEAL_TO_CONTACT,
                            }
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def create_note(self, body: str, deal_id: str) -> str:
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/notes",
            headers=self._headers(),
            json={
                "properties": {
                    "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                    "hs_note_body": body,
                },
                "associations": [
                    {
                        "to": {"id": deal_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": ASSOC_NOTE_TO_DEAL,
                            }
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]
