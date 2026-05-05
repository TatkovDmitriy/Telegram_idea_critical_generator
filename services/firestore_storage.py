import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType


def _init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.environ["FIREBASE_PROJECT_ID"],
            "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
            "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
    return firestore.client()


class FirestoreStorage(BaseStorage):
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = _init_firebase()
        return self._db

    def _doc_ref(self, key: StorageKey):
        doc_id = f"{key.chat_id}_{key.user_id}"
        return self.db.collection("bot_sessions").document(doc_id)

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if state else None
        self._doc_ref(key).set({"state": value}, merge=True)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        doc = self._doc_ref(key).get()
        return doc.to_dict().get("state") if doc.exists else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        self._doc_ref(key).set({"data": data}, merge=True)

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        doc = self._doc_ref(key).get()
        return doc.to_dict().get("data", {}) if doc.exists else {}

    async def close(self) -> None:
        pass
