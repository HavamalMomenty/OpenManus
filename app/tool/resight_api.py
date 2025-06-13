import httpx
import os
import pandas as pd
from typing import Any, Dict, Optional, List
from datetime import datetime

from app.tool.base import BaseTool, ToolResult, ToolFailure
from app.logger import logger

# --- Configuration ---
RESIGHT_API_BASE_URL = config.get("resights.base_url", "https://api.resights.dk/api/v2")
RESIGHT_API_KEY = config.get("resights.api_key")
#RESIGHT_API_BASE_URL = os.getenv("RESIGHT_API_BASE_URL", "https://api.resights.dk/api/v2")
#RESIGHT_API_KEY = os.getenv("RESIGHT_API_KEY")

# --- Constants for FetchResightPropertyTableTool ---
ALL_AVAILABLE_PROCESSED_FIELDS = [
    "propertyId", "bfe_number", "bbr.units.id", "units.status",
    "bbr.units.enh020_unit_usage", "bbr.units.enh026_area_unit_total",
    "bbr.units.enh027_area_residential", "bbr.units.enh028_area_commercial",
    "bbr.units.enh031_number_rooms", "bbr.buildings.id", "timestamp"
]
DEFAULT_OUTPUT_FIELDS = ALL_AVAILABLE_PROCESSED_FIELDS # Or a subset if preferred

# --- Specialized High-Level Tool ---
class FetchResightPropertyTableTool(BaseTool):
    name: str = "fetch_resight_property_table"
    description: str = (
        "Fetches detailed property data for a given Danish BFE number (BFE-nummer) from the Resights API. "
        "It processes the raw JSON and returns a structured, cleaned table (as a JSON string) with key information about the property's units and buildings. "
        "You can specify which data fields you want in the output."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "bfe_number": {
                "type": "integer",
                "description": "The BFE number (Bolig- og Bygningsregisterets Ejendomsnummer) of the property to look up. Example: 6022110."
            },
            "output_fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ALL_AVAILABLE_PROCESSED_FIELDS
                },
                "description": (
                    "Optional. A list of specific fields to include in the output table. "
                    "If not provided, a default set of all available fields will be returned. "
                    f"Choose from the available fields: {', '.join(ALL_AVAILABLE_PROCESSED_FIELDS)}."
                )
            }
        },
        "required": ["bfe_number"]
    }

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not RESIGHT_API_KEY:
            logger.warning("RESIGHT_API_KEY environment variable is not set. FetchResightPropertyTableTool will fail.")

    async def execute(self, bfe_number: int, output_fields: Optional[List[str]] = None) -> ToolResult:
        if not RESIGHT_API_KEY:
            return ToolFailure(error="Resight API key is not configured. Set the RESIGHT_API_KEY environment variable.")

        url = f"{RESIGHT_API_BASE_URL.rstrip('/')}/properties/{bfe_number}"
        headers = {"Authorization": RESIGHT_API_KEY} # Assumes key is the token itself

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"Fetching property data for BFE: {bfe_number}")
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            logger.info(f"Processing data for BFE: {bfe_number}")
            propertyId = data.get("id")
            bfe_num_from_api = data.get("bfe_number", None)

            bbr = data.get("bbr", {})
            units_data = bbr.get("units", [])
            buildings_data = bbr.get("buildings", [])

            units_df = pd.DataFrame(units_data if units_data else [])
            if not units_df.empty:
                rename_units = {
                    "id": "bbr.units.id", "status": "units.status",
                    "enh020_unit_usage": "bbr.units.enh020_unit_usage",
                    "enh026_area_unit_total": "bbr.units.enh026_area_unit_total",
                    "enh027_area_residential": "bbr.units.enh027_area_residential",
                    "enh028_area_commercial": "bbr.units.enh028_area_commercial",
                    "enh031_number_rooms": "bbr.units.enh031_number_rooms"
                }
                units_df.rename(columns=rename_units, inplace=True)

            buildings_df = pd.DataFrame(buildings_data if buildings_data else [])
            if not buildings_df.empty:
                buildings_df.rename(columns={"id": "bbr.buildings.id"}, inplace=True)

            merged_df = pd.DataFrame() # Initialize an empty DataFrame
            if not units_df.empty and not buildings_df.empty:
                units_df["_crossjoin_key"] = 1
                buildings_df["_crossjoin_key"] = 1
                merged_df = pd.merge(units_df, buildings_df, on="_crossjoin_key").drop("_crossjoin_key", axis=1)
            elif not units_df.empty:
                merged_df = units_df
            elif not buildings_df.empty:
                merged_df = buildings_df

            if merged_df.empty and (not units_data and not buildings_data):
                 return ToolResult(output=f"No BBR units or buildings data found for BFE {bfe_number}. Raw property ID: {propertyId}")

            # Add common identifiers and timestamp
            merged_df["propertyId"] = propertyId
            merged_df["bfe_number"] = bfe_num_from_api if bfe_num_from_api is not None else bfe_number
            merged_df["timestamp"] = datetime.now().isoformat()

            # Determine final columns based on user request or defaults
            columns_to_select = []
            if output_fields:
                for field in output_fields:
                    if field in ALL_AVAILABLE_PROCESSED_FIELDS:
                        if field in merged_df.columns:
                            columns_to_select.append(field)
                        else:
                            logger.warning(f"Requested field '{field}' is valid but not present in processed data for BFE {bfe_number}. Skipping.")
                    else:
                        logger.warning(f"Requested field '{field}' is not a valid available field. Skipping.")
                if not columns_to_select: # If all requested fields were invalid/missing
                    logger.warning(f"No valid/available fields from request for BFE {bfe_number}. Returning default fields.")
                    columns_to_select = [col for col in DEFAULT_OUTPUT_FIELDS if col in merged_df.columns]
            else:
                columns_to_select = [col for col in DEFAULT_OUTPUT_FIELDS if col in merged_df.columns]

            if not columns_to_select and not merged_df.empty : # If still no columns but dataframe has data (e.g. only propertyId)
                 logger.info(f"No specific BBR unit/building columns selected for BFE {bfe_number}, but base property data exists.")
                 # Ensure essential IDs are present if nothing else matches
                 if "propertyId" not in merged_df.columns and propertyId: merged_df["propertyId"] = propertyId
                 if "bfe_number" not in merged_df.columns: merged_df["bfe_number"] = bfe_num_from_api if bfe_num_from_api is not None else bfe_number
                 if "timestamp" not in merged_df.columns: merged_df["timestamp"] = datetime.now().isoformat()
                 columns_to_select = [col for col in ["propertyId", "bfe_number", "timestamp"] if col in merged_df.columns]

            if not columns_to_select and merged_df.empty:
                # This case means no units, no buildings, and merged_df was never populated with base IDs
                return ToolResult(output=f"No data could be processed or selected for BFE {bfe_number}. Property ID: {propertyId}")

            final_df = merged_df[columns_to_select].copy()
            return ToolResult(output=final_df.to_json(orient='records', date_format='iso'))

        except httpx.HTTPStatusError as e:
            error_message = f"Resight API HTTP error for BFE {bfe_number}: {e.response.status_code} - {e.response.text}"
            logger.error(error_message)
            return ToolFailure(error=error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred while fetching property data for BFE {bfe_number}: {str(e)}"
            logger.error(error_message, exc_info=True)
            return ToolFailure(error=error_message)


# --- Generic Low-Level Tool (Unchanged) ---

class ResightApiTool(BaseTool):
    name: str = "call_resight_api"
    description: str = (
        "A low-level tool to call any REST endpoint on the Resight API. "
        "Use this for endpoints other than fetching property data by BFE number. For that, use 'fetch_resight_property_table'."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "endpoint_path": {
                "type": "string",
                "description": "The specific API path (e.g., '/persons/search' or '/company/12345678')."
            },
            "method": {
                "type": "string",
                "description": "HTTP method.",
                "enum": ["GET", "POST", "PUT", "DELETE"]
            },
            "query_params": {
                "type": "object",
                "description": "Optional. Dictionary of URL query parameters.",
            },
            "json_payload": {
                "type": "object",
                "description": "Optional. Dictionary for the JSON body of POST/PUT requests."
            }
        },
        "required": ["endpoint_path", "method"]
    }

    async def execute(self, endpoint_path: str, method: str, query_params: Optional[Dict[str, str]] = None, json_payload: Optional[Dict[str, Any]] = None) -> ToolResult:
        if not RESIGHT_API_KEY:
            return ToolFailure(error="Resight API key is not configured.")

        full_url = f"{RESIGHT_API_BASE_URL.rstrip('/')}/{endpoint_path.lstrip('/')}"
        headers = {"Authorization": RESIGHT_API_KEY, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method.upper(), full_url, headers=headers, params=query_params, json=json_payload
                )
                response.raise_for_status()
                if response.status_code == 204:
                    return ToolResult(output={"status": "success", "message": "Operation successful, no content returned."})
                return ToolResult(output=response.json())
        except httpx.HTTPStatusError as e:
            return ToolFailure(error=f"Resight API HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return ToolFailure(error=f"An unexpected error occurred: {str(e)}")
