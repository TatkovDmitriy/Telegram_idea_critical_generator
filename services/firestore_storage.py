import os
import time
from typing import Any, Dict, Optional

import httpx
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

FIRESTORE_BASE = "https://firestore.googleapis.com/v1"
SCOPES = ["https://www.googleapis.com/auth/datastore"]


def _build_cred_info() -> dict:
    return {
        "type": "service_account",
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "token_uri": "https://oauth2.googleapis.com/token",
    }


def _to_fs(val) -> dict:
    if val is None:
        return {"nullValue": None}
    if isinstance(val, bool):
        return {"booleanValue": val}
    if isinstance(val, int):
        return {"integerValue": str(val)}
    if isinstance(val, str):
        return {"stringValue": val}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {k: _to_fs(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def _from_fs(val: dict):
    if "nullValue" in val:
        return None
    if "stringValue" in val:
        return val["stringValue"]
    if "booleanValue" in val:
        return val["booleanValue"]
    if "integerValue" in val:
        return int(val["integerValue"])
    if "mapValue" in val:
        return {k: _from_fs(v) for k, v in val["mapValue"].get("fields", {}).items()}
    return None


class FirestoreStorage(BaseStorage):
    def __init__(self):
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._project_id = os.environ["FIREBASE_PROJECT_ID"]

    def _refresh_token(self):
        if self._token and time.time() < self._token_expiry - 60:
            return
        creds = service_account.Credentials.from_service_account_info(
            _build_cred_info(), scopes=SCOPES
        )
        creds.refresh(GoogleRequest())
        self._token = creds.token
        self._token_expiry = time.time() + 3600

    def _headers(self) -> dict:
        self._refresh_token()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _doc_url(self, key: StorageKey) -> str:
        doc_id = f"{key.chat_id}_{key.user_id}"
        return f"{FIRESTORE_BASE}/projects/{self._project_id}/databases/(default)/documents/bot_sessions/{doc_id}"

    async def _get_doc(self, key: StorageKey) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(self._doc_url(key), headers=self._headers())
            if resp.status_code == 404:
                return {}
            resp.raise_for_status()
            return {k: _from_fs(v) for k, v in resp.json().get("fields", {}).items()}

    async def _patch_doc(self, key: StorageKey, data: dict):
        fields = {k: _to_fs(v) for k, v in data.items()}
        mask = "&".join(f"updateMask.fieldPaths={k}" for k in data)
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{self._doc_url(key)}?{mask}",
                headers=self._headers(),
                json={"fields": fields},
            )
            resp.raise_for_status()

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await self._patch_doc(key, {"state": state.state if state else None})

    async def get_state(self, key: StorageKey) -> Optional[str]:
        return (await self._get_doc(key)).get("state")

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        await self._patch_doc(key, {"data": data})

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        return (await self._get_doc(key)).get("data", {})

    async def close(self) -> None:
        pass
