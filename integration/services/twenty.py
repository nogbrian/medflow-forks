"""
Twenty CRM API Client.

Handles all communication with Twenty CRM for:
- Contacts (people)
- Companies
- Opportunities (pipeline)
- Workspaces (multi-tenant)

Docs: https://docs.twenty.com/api
"""

import logging
from typing import Any

import httpx

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TwentyAPIError(Exception):
    """Twenty API error with status code and details."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class TwentyClient:
    """
    HTTP client for Twenty CRM GraphQL API.

    Usage:
        client = TwentyClient(api_key="...", workspace_id="...")
        contacts = await client.list_contacts(limit=50)
    """

    def __init__(
        self,
        api_key: str | None = None,
        workspace_id: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.twenty_api_key
        self.workspace_id = workspace_id
        self.base_url = (base_url or settings.twenty_api_url).rstrip("/")
        self.graphql_url = f"{self.base_url}/graphql"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            if self.workspace_id:
                headers["X-Workspace-Id"] = self.workspace_id

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _graphql(self, query: str, variables: dict | None = None) -> dict:
        """Execute GraphQL query against Twenty API."""
        client = await self._get_client()
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = await client.post(self.graphql_url, json=payload)
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_msg = data["errors"][0].get("message", "GraphQL error")
                raise TwentyAPIError(error_msg, status_code=400, details=data["errors"])

            return data.get("data", {})
        except httpx.HTTPStatusError as e:
            raise TwentyAPIError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise TwentyAPIError(f"Request failed: {str(e)}")

    # =========================================================================
    # CONTACTS (People)
    # =========================================================================

    async def list_contacts(
        self,
        limit: int = 50,
        cursor: str | None = None,
        filter_: dict | None = None,
    ) -> dict:
        """List contacts (people) with pagination."""
        query = """
        query ListPeople($first: Int, $after: String, $filter: PersonFilterInput) {
            people(first: $first, after: $after, filter: $filter) {
                edges {
                    node {
                        id
                        name { firstName lastName }
                        email { primaryEmail }
                        phone { primaryPhoneNumber }
                        company { id name }
                        createdAt
                        updatedAt
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        variables = {"first": limit}
        if cursor:
            variables["after"] = cursor
        if filter_:
            variables["filter"] = filter_

        data = await self._graphql(query, variables)
        return data.get("people", {})

    async def get_contact(self, contact_id: str) -> dict | None:
        """Get a single contact by ID."""
        query = """
        query GetPerson($id: UUID!) {
            person(id: $id) {
                id
                name { firstName lastName }
                email { primaryEmail additionalEmails }
                phone { primaryPhoneNumber additionalPhones }
                company { id name }
                linkedinLink { url }
                xLink { url }
                jobTitle
                city
                createdAt
                updatedAt
            }
        }
        """
        data = await self._graphql(query, {"id": contact_id})
        return data.get("person")

    async def create_contact(
        self,
        first_name: str,
        last_name: str = "",
        email: str | None = None,
        phone: str | None = None,
        company_id: str | None = None,
        **extra_fields,
    ) -> dict:
        """Create a new contact."""
        mutation = """
        mutation CreatePerson($data: PersonCreateInput!) {
            createPerson(data: $data) {
                id
                name { firstName lastName }
                email { primaryEmail }
                phone { primaryPhoneNumber }
            }
        }
        """
        data = {
            "name": {"firstName": first_name, "lastName": last_name},
        }
        if email:
            data["email"] = {"primaryEmail": email}
        if phone:
            data["phone"] = {"primaryPhoneNumber": phone}
        if company_id:
            data["companyId"] = company_id
        data.update(extra_fields)

        result = await self._graphql(mutation, {"data": data})
        return result.get("createPerson", {})

    async def update_contact(self, contact_id: str, **fields) -> dict:
        """Update a contact."""
        mutation = """
        mutation UpdatePerson($id: UUID!, $data: PersonUpdateInput!) {
            updatePerson(id: $id, data: $data) {
                id
                name { firstName lastName }
                email { primaryEmail }
                updatedAt
            }
        }
        """
        result = await self._graphql(mutation, {"id": contact_id, "data": fields})
        return result.get("updatePerson", {})

    # =========================================================================
    # COMPANIES
    # =========================================================================

    async def list_companies(
        self,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict:
        """List companies with pagination."""
        query = """
        query ListCompanies($first: Int, $after: String) {
            companies(first: $first, after: $after) {
                edges {
                    node {
                        id
                        name
                        domainName { primaryLinkUrl }
                        employees
                        createdAt
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        data = await self._graphql(query, {"first": limit, "after": cursor})
        return data.get("companies", {})

    async def create_company(
        self,
        name: str,
        domain: str | None = None,
        **extra_fields,
    ) -> dict:
        """Create a new company."""
        mutation = """
        mutation CreateCompany($data: CompanyCreateInput!) {
            createCompany(data: $data) {
                id
                name
                domainName { primaryLinkUrl }
            }
        }
        """
        data = {"name": name}
        if domain:
            data["domainName"] = {"primaryLinkUrl": domain}
        data.update(extra_fields)

        result = await self._graphql(mutation, {"data": data})
        return result.get("createCompany", {})

    # =========================================================================
    # OPPORTUNITIES (Pipeline)
    # =========================================================================

    async def list_opportunities(
        self,
        limit: int = 50,
        stage: str | None = None,
    ) -> dict:
        """List opportunities with optional stage filter."""
        query = """
        query ListOpportunities($first: Int, $filter: OpportunityFilterInput) {
            opportunities(first: $first, filter: $filter) {
                edges {
                    node {
                        id
                        name
                        stage
                        amount { amountMicros currencyCode }
                        closeDate
                        probability
                        company { id name }
                        pointOfContact { id name { firstName lastName } }
                        createdAt
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        variables: dict = {"first": limit}
        if stage:
            variables["filter"] = {"stage": {"eq": stage}}

        data = await self._graphql(query, variables)
        return data.get("opportunities", {})

    async def create_opportunity(
        self,
        name: str,
        stage: str = "NEW",
        amount: int | None = None,
        currency: str = "BRL",
        company_id: str | None = None,
        contact_id: str | None = None,
        **extra_fields,
    ) -> dict:
        """Create a new opportunity."""
        mutation = """
        mutation CreateOpportunity($data: OpportunityCreateInput!) {
            createOpportunity(data: $data) {
                id
                name
                stage
                amount { amountMicros currencyCode }
            }
        }
        """
        data: dict = {"name": name, "stage": stage}
        if amount:
            data["amount"] = {"amountMicros": amount * 1_000_000, "currencyCode": currency}
        if company_id:
            data["companyId"] = company_id
        if contact_id:
            data["pointOfContactId"] = contact_id
        data.update(extra_fields)

        result = await self._graphql(mutation, {"data": data})
        return result.get("createOpportunity", {})

    async def update_opportunity_stage(
        self,
        opportunity_id: str,
        stage: str,
    ) -> dict:
        """Update opportunity stage."""
        mutation = """
        mutation UpdateOpportunity($id: UUID!, $data: OpportunityUpdateInput!) {
            updateOpportunity(id: $id, data: $data) {
                id
                name
                stage
                updatedAt
            }
        }
        """
        result = await self._graphql(
            mutation,
            {"id": opportunity_id, "data": {"stage": stage}},
        )
        return result.get("updateOpportunity", {})

    # =========================================================================
    # WEBHOOKS
    # =========================================================================

    async def register_webhook(
        self,
        url: str,
        events: list[str],
        description: str = "MedFlow Integration",
    ) -> dict:
        """Register a webhook for events."""
        mutation = """
        mutation CreateWebhook($data: WebhookCreateInput!) {
            createWebhook(data: $data) {
                id
                targetUrl
                operations
                isActive
            }
        }
        """
        result = await self._graphql(
            mutation,
            {
                "data": {
                    "targetUrl": url,
                    "operations": events,
                    "description": description,
                }
            },
        )
        return result.get("createWebhook", {})
