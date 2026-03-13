import base64
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_REPO = "Chakrapani2122/Regen-Ag-Data"


class GitHubClient:
    def __init__(self, token: str, repo: str = DEFAULT_REPO):
        self.token = token
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "PUT", "POST", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _headers(self, accept: Optional[str] = None) -> Dict[str, str]:
        headers = {"Authorization": f"token {self.token}"}
        if accept:
            headers["Accept"] = accept
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        accept: Optional[str] = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> Tuple[Optional[requests.Response], Optional[str], bool]:
        url = f"{self.api_base}{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                headers=self._headers(accept=accept),
                timeout=timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            return None, f"Network error: {exc}", False

        if response.status_code in (401, 403):
            return response, "Authentication failed or token access denied.", True

        return response, None, False

    def validate_token(self) -> bool:
        response, _, auth_error = self._request("GET", "", timeout=20)
        return bool(response is not None and response.status_code == 200 and not auth_error)

    def list_contents(self, path: str = "") -> Tuple[Optional[list], Optional[str], bool]:
        encoded_path = quote(path, safe='/') if path else ""
        endpoint = f"/contents/{encoded_path}" if encoded_path else "/contents"
        response, error, auth_error = self._request("GET", endpoint)
        if response is None:
            return None, error, auth_error
        if response.status_code != 200:
            return None, f"GitHub returned status {response.status_code} for {endpoint}.", auth_error

        try:
            return response.json(), None, False
        except ValueError:
            return None, "Invalid JSON returned by GitHub.", False

    def get_file_metadata(self, file_path: str) -> Tuple[Optional[dict], Optional[str], bool]:
        encoded_file_path = quote(file_path, safe='/')
        endpoint = f"/contents/{encoded_file_path}"
        response, error, auth_error = self._request("GET", endpoint)
        if response is None:
            return None, error, auth_error
        if response.status_code != 200:
            return None, f"GitHub returned status {response.status_code} for metadata.", auth_error

        try:
            return response.json(), None, False
        except ValueError:
            return None, "Invalid JSON returned by GitHub metadata endpoint.", False

    def get_file_content(self, file_path: str) -> Tuple[Optional[bytes], Optional[str], bool, Optional[dict]]:
        metadata, error, auth_error = self.get_file_metadata(file_path)
        if metadata is None:
            return None, error, auth_error, None

        if metadata.get("encoding") == "base64" and metadata.get("content"):
            try:
                return base64.b64decode(metadata["content"]), None, False, metadata
            except Exception as exc:
                return None, f"Failed to decode base64 content: {exc}", False, metadata

        download_url = metadata.get("download_url")
        if download_url:
            try:
                response = self.session.get(
                    download_url,
                    headers=self._headers(),
                    timeout=60,
                )
                if response.status_code in (401, 403):
                    return None, "Authentication failed or token access denied.", True, metadata
                if response.status_code == 200:
                    return response.content, None, False, metadata
            except requests.RequestException as exc:
                return None, f"Download URL request failed: {exc}", False, metadata

        encoded_file_path = quote(file_path, safe='/')
        endpoint = f"/contents/{encoded_file_path}"
        response, error, auth_error = self._request(
            "GET",
            endpoint,
            accept="application/vnd.github.raw",
            timeout=60,
        )
        if response is None:
            return None, error, auth_error, metadata
        if response.status_code != 200:
            return None, f"GitHub raw content request returned status {response.status_code}.", auth_error, metadata

        return response.content, None, False, metadata

    def put_file(
        self,
        file_path: str,
        message: str,
        content_b64: str,
        sha: Optional[str] = None,
        extra_fields: Optional[dict] = None,
    ) -> Tuple[Optional[dict], Optional[str], bool]:
        encoded_file_path = quote(file_path, safe='/')
        endpoint = f"/contents/{encoded_file_path}"
        payload = {
            "message": message,
            "content": content_b64,
        }
        if sha:
            payload["sha"] = sha
        if extra_fields:
            payload.update(extra_fields)

        response, error, auth_error = self._request("PUT", endpoint, json=payload, timeout=60)
        if response is None:
            return None, error, auth_error
        if response.status_code not in (200, 201):
            return None, f"GitHub returned status {response.status_code} while uploading.", auth_error

        try:
            return response.json(), None, False
        except ValueError:
            return {}, None, False


@st.cache_resource(show_spinner=False)
def get_github_client(token: str, repo: str = DEFAULT_REPO) -> GitHubClient:
    # Tiny sleep helps reduce rapid duplicate session creation on very fast reruns.
    time.sleep(0.01)
    return GitHubClient(token=token, repo=repo)
