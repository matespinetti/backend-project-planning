import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BonitaClient:
    """
    Async client for interacting with Bonita BPM REST API.

    Key points:
    - Use httpx.AsyncClient cookie jar (no manual Cookie header).
    - After login, read X-Bonita-API-Token cookie and send it as a header on every API call.
    - For instantiation, send {"variables": [{"name":"...", "value": ...}, ...]}.
    - Must be used as async context manager or manually closed.
    """

    def __init__(self, timeout: float = 20.0):
        self.base_url = settings.BONITA_URL.rstrip("/")
        self.username = settings.BONITA_USERNAME
        self.password = settings.BONITA_PASSWORD
        self.process_name = settings.BONITA_PROCESS_NAME

        # Persist connection + cookies across requests
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._api_token: Optional[str] = None

    # ---------- Internal utils ----------

    def _headers(self) -> Dict[str, str]:
        """Common headers including CSRF token if present."""
        headers = {"Content-Type": "application/json"}
        if self._api_token:
            headers["X-Bonita-API-Token"] = self._api_token
        return headers

    def _extract_api_token_from_cookies(self) -> Optional[str]:
        """
        Bonita sets 'X-Bonita-API-Token' as a cookie after successful login.
        You must echo it back in the 'X-Bonita-API-Token' header.
        """
        try:
            return self.client.cookies.get("X-Bonita-API-Token")
        except Exception:
            return None

    async def _ensure_session(self) -> None:
        """Ensure we are logged in and have a valid API token."""
        if self._api_token:
            return
        ok = await self.login()
        if not ok:
            raise RuntimeError("Bonita login failed")

    async def _retry_on_401(self, func, *args, **kwargs):
        """
        Helper to retry once on 401/403 by re-authenticating transparently.
        """
        resp = await func(*args, **kwargs)
        if resp.status_code in (401, 403):
            logger.info("Auth expired or forbidden. Re-authenticating...")
            if not await self.login():
                raise RuntimeError("Re-authentication with Bonita failed")
            resp = await func(*args, **kwargs)
        return resp

    # ---------- Auth ----------

    async def login(self) -> bool:
        """
        Authenticate with Bonita:
        - POST /loginservice with form-encoded data (redirect=false).
        - Grab X-Bonita-API-Token from cookies for subsequent API calls.
        """
        try:
            url = f"{self.base_url}/loginservice"
            data = {
                "username": self.username,
                "password": self.password,
                "redirect": "false",
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            resp = await self.client.post(url, data=data, headers=headers)
            if resp.status_code not in (200, 204):
                logger.error(f"Bonita login failed: {resp.status_code} - {resp.text}")
                return False

            token = self._extract_api_token_from_cookies()
            if not token:
                # Some setups require fetching the session endpoint to populate cookies
                sess = await self.client.get(f"{self.base_url}/API/system/session")
                token = self._extract_api_token_from_cookies()

            if token:
                self._api_token = token
                logger.info("Authenticated with Bonita; API token acquired.")
                return True
            else:
                logger.error("Login succeeded but no X-Bonita-API-Token cookie found.")
                return False
        except Exception as e:
            logger.exception(f"Error during Bonita login: {e}")
            return False

    # ---------- BPM endpoints ----------

    async def get_process_definition(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest ENABLED process definition by name.
        """
        try:
            await self._ensure_session()

            url = f"{self.base_url}/API/bpm/process"
            params = {
                "p": 0,
                "c": 1,
                # Filters are repeated as separate 'f' params in Bonita
                "f": ["name=" + self.process_name, "activationState=ENABLED"],
                # Get the newest version first
                "o": "version DESC",
            }

            # httpx doesn't expand list params automatically with dict literal,
            # so build params properly:
            query_params: List[tuple] = [("p", 0), ("c", 1), ("o", "version DESC")]
            for f in params["f"]:
                query_params.append(("f", f))

            async def _call():
                return await self.client.get(
                    url, params=query_params, headers=self._headers()
                )

            resp = await self._retry_on_401(_call)
            if resp.status_code == 200:
                processes = resp.json()
                if processes:
                    proc = processes[0]
                    logger.info(
                        f"Found process: {proc.get('name')} v{proc.get('version')}"
                    )
                    return proc
                logger.error(f"Process '{self.process_name}' not found or not ENABLED.")
                return None

            logger.error(
                f"Failed to get process definition: {resp.status_code} - {resp.text}"
            )
            return None
        except Exception as e:
            logger.exception(f"Error getting process definition: {e}")
            return None

    async def start_process(
        self,
        contract_inputs: Dict[str, Any],
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a process instance by sending START CONTRACT inputs.
        Optionally set case variables right after the case is created.

        contract_inputs: dict like {"project_id": "..."}  # keys MUST match Bonita start contract
        initial_variables: dict like {"status": "PENDING"}  # optional case vars set post-start
        """
        try:
            proc = await self.get_process_definition()
            if not proc:
                return None

            process_id = proc["id"]
            url = f"{self.base_url}/API/bpm/process/{process_id}/instantiation"

            async def _call():
                # IMPORTANT: send the contract as a flat JSON object
                return await self.client.post(
                    url, json=contract_inputs, headers=self._headers()
                )

            resp = await self._retry_on_401(_call)

            if resp.status_code == 200:
                data = resp.json()
                case_id = data.get("caseId")

                # Optionally set initial case variables AFTER the case exists
                if initial_variables and case_id:
                    for k, v in initial_variables.items():
                        ok = await self.set_case_variable(case_id, k, v)
                        if not ok:
                            logger.warning(f"Failed to set initial variable {k}")

                logger.info(f"Process instance started. caseId={case_id}")
                return data

            logger.error(f"Failed to start process: {resp.status_code} - {resp.text}")
            return None

        except Exception as e:
            logger.exception(f"Error starting process: {e}")
            return None

    async def set_case_variable(
        self,
        case_id: str,
        variable_name: str,
        value: Any,
        var_type: Optional[str] = None,
    ) -> bool:
        """
        Set a case variable value.

        var_type: If provided, use a Bonita type name (e.g., 'java.lang.String',
        'java.lang.Integer', 'java.lang.Boolean'). If omitted, a best-effort inference is used.
        """
        try:
            await self._ensure_session()

            url = f"{self.base_url}/API/bpm/caseVariable/{case_id}/{variable_name}"

            if var_type is None:
                # naive inference
                if isinstance(value, bool):
                    var_type = "java.lang.Boolean"
                elif isinstance(value, int):
                    var_type = "java.lang.Integer"
                elif isinstance(value, float):
                    var_type = "java.lang.Double"
                else:
                    var_type = "java.lang.String"

            body = {"type": var_type, "value": value}

            async def _call():
                return await self.client.put(url, json=body, headers=self._headers())

            resp = await self._retry_on_401(_call)
            if resp.status_code == 200:
                logger.info(f"Case variable set: {variable_name}={value} ({var_type})")
                return True

            logger.error(
                f"Failed to set case variable: {resp.status_code} - {resp.text}"
            )
            return False
        except Exception as e:
            logger.exception(f"Error setting case variable: {e}")
            return False

    async def aclose(self):
        """Close the async client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
