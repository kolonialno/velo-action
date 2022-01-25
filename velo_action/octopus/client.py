import logging
import urllib.parse
from functools import lru_cache

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(name="octopus")


class OctopusClient:
    _baseurl: str = ""
    _cached_environment_ids: dict = {}
    _cached_tenant_ids: dict = {}
    _headers: dict = {}

    def __init__(self, server=None, api_key=None):
        self._baseurl = server
        self._headers = {"X-Octopus-ApiKey": f"{api_key}"}
        self._verify_connection()

    def base_url(self):
        return self._baseurl

    def get(self, path):
        """
        Get a resource

        Returns parsed JSON on success.
        Raises RuntimeError otherwise.
        """
        return self._request("get", path)

    def head(self, path) -> bool:
        """
        Check existence of a resource

        Returns boolean.
        Raises RuntimeError.
        """
        return bool(self._request("head", path))

    def post(self, path, data):
        """
        Create a new resource

        Returns parsed JSON on success.
        Raises RuntimeError otherwise.
        """
        return self._request("post", path, data)

    def lookup_environment_id(self, env_name) -> str:
        """Translate project name into a project id"""
        if not self._cached_environment_ids:
            data = self.get("api/environments/all")
            self._cached_environment_ids = {e["Name"]: e["Id"] for e in data}
        return self._cached_environment_ids.get(env_name, "")

    @lru_cache
    def lookup_project_id(self, project_name) -> str:
        """Translate project name into a project id"""
        return self.get(f"api/projects/{project_name}").get("Id")

    def lookup_tenant_id(self, tenant_name) -> str:
        """Translate tenant name into a tenant id"""
        if not tenant_name:
            return ""

        if not self._cached_tenant_ids:
            data = self.get("api/tenants/all")
            self._cached_tenant_ids = {e["Name"]: e["Id"] for e in data}
        return self._cached_tenant_ids.get(tenant_name, "")

    def _request(self, method, path, data=None):
        url = urllib.parse.urljoin(self._baseurl, path)
        try:
            response = requests.request(method, url, json=data, headers=self._headers)
            logger.debug(
                f"{response.request.method} {response.url}: {response.status_code}"
            )
        except RequestException as err:
            raise RuntimeError(f"Error connecting to '{url}'. Invalid URL?") from err
        return self._handle_response(response)

    def _verify_connection(self):
        try:
            self._request("head", "api")
        except requests.RequestException as err:
            logger.error(
                "Could not establish connection with Octopus deploy server "
                f"at '{self._baseurl}'. Failed with '{err}'"
            )
        logger.debug(
            f"Successfully connected to Octopus deploy server '{self._baseurl}'"
        )

    @staticmethod
    def _handle_response(response):
        if 200 <= response.status_code < 300:
            if not response.content:
                return True
            return response.json()

        elif 400 <= response.status_code < 600:
            if not response.content:
                return False
            data = response.json()
            err: str = f"{response.reason}: " + data.get(
                "ErrorMessage", "Unknown error"
            )

            errors = data.get("Errors", [])
            if errors:
                err = err + f" {'. '.join(errors)}"

            help_links = data.get("ParsedHelpLinks")
            if help_links:
                err = err + f" ({help_links})"
            raise RuntimeError(err)

        else:
            raise RuntimeError(
                f"{response.request.method} '{response.url}' failed with status "
                f"'{response.status_code}'"
            )
