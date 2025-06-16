import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from app.tool.base import BaseTool, ToolFailure, ToolResult
from app.logger import logger
from app.config import config

# --- Configuration ---------------------------------------------------------
RESIGHT_API_BASE_URL = config.resights_config.base_url.rstrip("/")
RESIGHT_API_KEY = config.resights_config.api_key or os.getenv("RESIGHT_API_KEY")
if not RESIGHT_API_KEY:
    logger.warning("RESIGHT_API_KEY er ikke sat – API-kald vil fejle.")

# --- Constants -------------------------------------------------------------
ALL_AVAILABLE_PROCESSED_FIELDS = [
    "propertyId",
    "bfe_number",
    "bbr.units.id",
    "units.status",
    "bbr.units.enh020_unit_usage",
    "bbr.units.enh026_area_unit_total",
    "bbr.units.enh027_area_residential",
    "bbr.units.enh028_area_commercial",
    "bbr.units.enh031_number_rooms",
    "bbr.buildings.id",
    "timestamp",
]
DEFAULT_OUTPUT_FIELDS = ALL_AVAILABLE_PROCESSED_FIELDS


# ---------------------------------------------------------------------------#
# Helper                                                                     #
# ---------------------------------------------------------------------------#
def _extract_property_id(item: dict) -> Optional[str]:
    """Return the property UUID if present at top level (no relation-ids)."""
    return item.get("id") or item.get("uuid") or item.get("property_id")
# ---------------------------------------------------------------------------#
# Main tool                                                                  #
# ---------------------------------------------------------------------------#
class FetchResightPropertyTableTool(BaseTool):
    name: str = "fetch_resight_property_table"
    description: str = (
        "Henter ejendomsdata fra Resights API ved BFE-nummer og returnerer JSON-tabel."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "bfe_number": {
                "type": "integer",
                "description": "BFE-nummer på ejendommen. "
                "Hvis det ikke angives, forsøges det læst fra konfigurationen.",
            },
            "output_fields": {
                "type": "array",
                "description": "Valgfri liste af felter til output.",
                "items": {"type": "string"},
            },
        },
        "required": [],
    }

    async def execute(self, bfe_number: Optional[int] = None,
                  output_fields: Optional[List[str]] = None) -> ToolResult:
    # 0) resolve bfe_number + check API key  … (unchanged) …

        headers = {"Authorization": f"Bearer {RESIGHT_API_KEY}"}
        async with httpx.AsyncClient(timeout=60) as client:
            r1 = await client.get(
                f"{RESIGHT_API_BASE_URL}/properties",
                headers=headers,
                params={"bfe_number": bfe_number},
            )
            if r1.status_code in (401, 403):
                return ToolFailure(error="Unauthorised – check API-nøglen.")
            r1.raise_for_status()

        payload = r1.json()
        items = payload.get("results") or payload.get("data") or payload.get("items", [])
        if not items:
            return ToolResult(output=f"Ingen ejendom fundet for BFE {bfe_number}")


        data = items[0]                     # ← same object curl shows
    # --- data-frame processing continues here exactly as before ---


        # -------------------------------------------------------------------
        # 3) Transform to dataframe
        # -------------------------------------------------------------------
        
        prop_id = data.get("id") 
        bbr = data.get("bbr", {})
        units = pd.DataFrame(bbr.get("units", []))
        buildings = pd.DataFrame(bbr.get("buildings", []))

        if not units.empty:
            units.rename(
                columns={
                    "id": "bbr.units.id",
                    "status": "units.status",
                    "enh020_unit_usage": "bbr.units.enh020_unit_usage",
                    "enh026_area_unit_total": "bbr.units.enh026_area_unit_total",
                    "enh027_area_residential": "bbr.units.enh027_area_residential",
                    "enh028_area_commercial": "bbr.units.enh028_area_commercial",
                    "enh031_number_rooms": "bbr.units.enh031_number_rooms",
                },
                inplace=True,
            )

        if not buildings.empty:
            buildings.rename(columns={"id": "bbr.buildings.id"}, inplace=True)

        # Cross-join hvis begge findes
        merged: pd.DataFrame
        if not units.empty and not buildings.empty:
            units["_key"] = 1
            buildings["_key"] = 1
            merged = pd.merge(units, buildings, on="_key").drop("_key", axis=1)
        else:
            merged = units if not units.empty else buildings

        if merged.empty and not (bbr.get("units") or bbr.get("buildings")):
            return ToolResult(
                output=f"Ingen BBR-data for BFE {bfe_number}. Ejendoms-ID: {prop_id}"
            )

        # Metadata
        merged["propertyId"] = prop_id
        merged["bfe_number"] = bfe_number
        merged["timestamp"] = datetime.now().isoformat()

        # Select columns
        if output_fields:
            cols = [f for f in output_fields if f in merged.columns]
            if not cols:
                logger.warning("Ingen ønskede felter fundet – bruger default.")
                cols = [c for c in DEFAULT_OUTPUT_FIELDS if c in merged.columns]
        else:
            cols = [c for c in DEFAULT_OUTPUT_FIELDS if c in merged.columns]

        final_df = merged[cols] if cols else merged
        return ToolResult(output=final_df.to_json(orient="records", date_format="iso"))


# ---------------------------------------------------------------------------#
# Generic API wrapper (unchanged except minor fixes)                         #
# ---------------------------------------------------------------------------#
class ResightApiTool(BaseTool):
    name: str = "call_resight_api"
    description: str = (
        "Generelt REST-kald til Resights API (brug fetch_resight_property_table til BFE-data)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "endpoint_path": {"type": "string"},
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE"],
            },
            "query_params": {"type": "object"},
            "json_payload": {"type": "object"},
            "test_api": {"type": "boolean"},
            "get_valuation": {"type": "boolean"},
        },
        "required": ["endpoint_path", "method"],
    }

    # ---------------------------------------------------------------------#
    async def test_api_token(self) -> ToolResult:
        url = "https://api.resights.dk/health"  # root path – /api/v2/health gives 404
        headers = {"Authorization": f"Bearer {RESIGHT_API_KEY}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    return ToolResult(output={"status": "ok", "details": r.json()})
                return ToolFailure(
                    error=f"API health-check failed: {r.status_code} – {r.text}"
                )
        except Exception as e:
            return ToolFailure(error=f"API health-check exception: {e}")

    # ---------------------------------------------------------------------#
    async def fetch_property_valuation(self, bfe_number: int) -> ToolResult:
        logger.debug(
            f"[DEBUG] Entered fetch_property_valuation with bfe_number: {bfe_number}"
        )
        headers = {"Authorization": f"Bearer {RESIGHT_API_KEY}"}
        async with httpx.AsyncClient(timeout=30) as client:
            # search first
            r1 = await client.get(
                f"{RESIGHT_API_BASE_URL}/properties",
                headers=headers,
                params={"bfe_number": bfe_number},
            )
            r1.raise_for_status()
            items = (
                r1.json().get("data")
                or r1.json().get("results")
                or r1.json().get("items", [])
            )
            if not items:
                return ToolFailure(error=f"Ingen ejendom for BFE {bfe_number}")

            prop_id = _extract_property_id(items[0])
            if not prop_id:
                return ToolFailure(error="Kunne ikke finde property-id til valuation.")

            # valuation endpoint
            val_url = f"{RESIGHT_API_BASE_URL}/properties/{prop_id}/valuations"
            r2 = await client.get(val_url, headers=headers)
            r2.raise_for_status()
            return ToolResult(output=r2.json())

    # ---------------------------------------------------------------------#
    async def execute(
        self,
        endpoint_path: str,
        method: str,
        query_params: Optional[Dict[str, str]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        test_api: bool = False,
        get_valuation: bool = False,
    ) -> ToolResult:
        if not RESIGHT_API_KEY:
            return ToolFailure(error="Resight API key er ikke konfigureret.")

        if test_api:
            return await self.test_api_token()

        if get_valuation:
            try:
                return await self.fetch_property_valuation(int(endpoint_path))
            except ValueError:
                return ToolFailure(error="Ugyldigt BFE-nummer til valuation.")

        full_url = f"{RESIGHT_API_BASE_URL}/{endpoint_path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {RESIGHT_API_KEY}"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.request(
                    method.upper(),
                    full_url,
                    headers=headers,
                    params=query_params,
                    json=json_payload,
                )
                r.raise_for_status()
                if r.status_code == 204:
                    return ToolResult(
                        output={"status": "success", "message": "No content"}
                    )
                return ToolResult(output=r.json())
        except httpx.HTTPStatusError as e:
            return ToolFailure(
                error=f"HTTP error: {e.response.status_code} – {e.response.text}"
            )
        except Exception as e:
            return ToolFailure(error=f"Unexpected error: {e}")
