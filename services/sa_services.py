"""CRUD operations for Kubernetes service accounts and their namespace assignments.

Functions in this module never commit. The caller owns the transaction:

    with engine.begin() as conn:
        account = create_service_account(conn, "billing-worker")
        add_service_account_to_namespace(conn, account["id"], namespace_id)
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TypedDict

import yaml
from sqlalchemy import Connection, and_, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import ColumnElement

from models import (
    managed_identity_subscriptions as assignments,
    namespaces,
    serviceaccounts as service_accounts,
)

# Kubernetes requires ServiceAccount names to be DNS-1123 subdomains.
_MAX_NAME_LENGTH = 253
_DNS1123_SUBDOMAIN = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*")


# --------------------------------------------------------------------------
# Types and errors
# --------------------------------------------------------------------------

class ServiceAccount(TypedDict):
    id: int
    name: str


class Namespace(TypedDict):
    id: int
    name: str


class Assignment(TypedDict):
    id: int
    service_account_id: int
    namespace_id: int


class NotFoundError(LookupError):
    """Raised when a requested record does not exist."""


class AlreadyExistsError(ValueError):
    """Raised when a record would duplicate an existing one."""


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_service_account_name(name: str) -> None:
    """Raise ValueError if `name` is not a valid Kubernetes ServiceAccount name."""
    if len(name) > _MAX_NAME_LENGTH or not _DNS1123_SUBDOMAIN.fullmatch(name):
        raise ValueError(
            f"Invalid service account name {name!r}: must be at most {_MAX_NAME_LENGTH} "
            "characters of lowercase letters, digits, '-' or '.', "
            "starting and ending with a letter or digit"
        )


# --------------------------------------------------------------------------
# Service accounts
# --------------------------------------------------------------------------

def create_service_account(conn: Connection, name: str) -> ServiceAccount:
    """
    Create a new service account.

    Raises:
        ValueError: If the name is not a valid Kubernetes name.
        AlreadyExistsError: If a service account with this name already exists.
    """
    validate_service_account_name(name)
    try:
        with conn.begin_nested():
            result = conn.execute(insert(service_accounts).values(name=name))
    except IntegrityError as exc:
        raise AlreadyExistsError(f"Service account {name!r} already exists") from exc
    return ServiceAccount(id=result.inserted_primary_key[0], name=name)


def get_service_account_by_id(conn: Connection, service_account_id: int) -> ServiceAccount:
    """Retrieve a service account by ID. Raises NotFoundError if missing."""
    return _get_service_account(
        conn,
        service_accounts.c.id == service_account_id,
        f"Service account {service_account_id} not found",
    )


def get_service_account_by_name(conn: Connection, name: str) -> ServiceAccount:
    """Retrieve a service account by name. Raises NotFoundError if missing."""
    return _get_service_account(
        conn,
        service_accounts.c.name == name,
        f"Service account {name!r} not found",
    )


def get_all_service_accounts(conn: Connection) -> list[ServiceAccount]:
    """Retrieve all service accounts, ordered by name."""
    rows = conn.execute(
        select(service_accounts.c.id, service_accounts.c.name)
        .order_by(service_accounts.c.name)
    )
    return [ServiceAccount(id=row.id, name=row.name) for row in rows]


def delete_service_account(conn: Connection, service_account_id: int) -> None:
    """
    Delete a service account. Its namespace assignments are removed by the
    ON DELETE CASCADE foreign key. Raises NotFoundError if missing.
    """
    result = conn.execute(
        delete(service_accounts).where(service_accounts.c.id == service_account_id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f"Service account {service_account_id} not found")


def _get_service_account(
    conn: Connection, condition: ColumnElement[bool], not_found_message: str
) -> ServiceAccount:
    row = conn.execute(
        select(service_accounts.c.id, service_accounts.c.name).where(condition)
    ).first()
    if row is None:
        raise NotFoundError(not_found_message)
    return ServiceAccount(id=row.id, name=row.name)


# --------------------------------------------------------------------------
# Namespaces
# --------------------------------------------------------------------------

def get_namespace_by_id(conn: Connection, namespace_id: int) -> Namespace:
    """Retrieve a namespace by ID. Raises NotFoundError if missing."""
    row = conn.execute(
        select(namespaces.c.id, namespaces.c.name).where(namespaces.c.id == namespace_id)
    ).first()
    if row is None:
        raise NotFoundError(f"Namespace {namespace_id} not found")
    return Namespace(id=row.id, name=row.name)


# --------------------------------------------------------------------------
# Namespace assignments
# --------------------------------------------------------------------------

def add_service_account_to_namespace(
    conn: Connection, service_account_id: int, namespace_id: int
) -> Assignment:
    """
    Assign a service account to a namespace.

    Raises:
        NotFoundError: If the service account or namespace does not exist.
        AlreadyExistsError: If the assignment already exists.
    """
    try:
        with conn.begin_nested():
            result = conn.execute(
                insert(assignments).values(
                    service_account_id=service_account_id, namespace_id=namespace_id
                )
            )
    except IntegrityError as exc:
        # Work out which constraint failed so the caller gets a useful error.
        get_service_account_by_id(conn, service_account_id)
        get_namespace_by_id(conn, namespace_id)
        raise AlreadyExistsError(
            f"Service account {service_account_id} is already in namespace {namespace_id}"
        ) from exc

    return Assignment(
        id=result.inserted_primary_key[0],
        service_account_id=service_account_id,
        namespace_id=namespace_id,
    )


def get_namespaces_for_service_account(
    conn: Connection, service_account_id: int
) -> list[Namespace]:
    """Retrieve the namespaces a service account is assigned to (empty list if none)."""
    rows = conn.execute(
        select(namespaces.c.id, namespaces.c.name)
        .join(assignments, assignments.c.namespace_id == namespaces.c.id)
        .where(assignments.c.service_account_id == service_account_id)
        .order_by(namespaces.c.name)
    )
    return [Namespace(id=row.id, name=row.name) for row in rows]


def get_service_accounts_in_namespace(
    conn: Connection, namespace_id: int
) -> list[ServiceAccount]:
    """Retrieve every service account assigned to a namespace (empty list if none)."""
    rows = conn.execute(
        select(service_accounts.c.id, service_accounts.c.name)
        .join(assignments, assignments.c.service_account_id == service_accounts.c.id)
        .where(assignments.c.namespace_id == namespace_id)
        .order_by(service_accounts.c.name)
    )
    return [ServiceAccount(id=row.id, name=row.name) for row in rows]


def remove_service_account_from_namespace(
    conn: Connection, service_account_id: int, namespace_id: int
) -> None:
    """Remove a service account from a namespace. Raises NotFoundError if not assigned."""
    result = conn.execute(
        delete(assignments).where(
            and_(
                assignments.c.service_account_id == service_account_id,
                assignments.c.namespace_id == namespace_id,
            )
        )
    )
    if result.rowcount == 0:
        raise NotFoundError(
            f"Service account {service_account_id} is not in namespace {namespace_id}"
        )


# --------------------------------------------------------------------------
# Kubernetes manifest generation
# --------------------------------------------------------------------------

def generate_service_account_manifests_yaml(conn: Connection, service_account_id: int) -> str:
    """
    Generate ServiceAccount manifests for one service account, one document per
    namespace it is assigned to. Returns an empty string if it has no namespaces.
    Raises NotFoundError if the service account does not exist.
    """
    account = get_service_account_by_id(conn, service_account_id)
    return _dump_manifests(
        _service_account_manifest(account["name"], namespace["name"])
        for namespace in get_namespaces_for_service_account(conn, service_account_id)
    )


def generate_namespace_manifests_yaml(conn: Connection, namespace_id: int) -> str:
    """
    Generate ServiceAccount manifests for every service account in a namespace.
    Returns an empty string if the namespace has none.
    Raises NotFoundError if the namespace does not exist.
    """
    namespace = get_namespace_by_id(conn, namespace_id)
    return _dump_manifests(
        _service_account_manifest(account["name"], namespace["name"])
        for account in get_service_accounts_in_namespace(conn, namespace_id)
    )


def _service_account_manifest(name: str, namespace: str) -> dict:
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {"name": name, "namespace": namespace},
    }


def _dump_manifests(manifests: Iterable[dict]) -> str:
    """Serialize manifests as a multi-document YAML stream ('---' separated)."""
    return yaml.safe_dump_all(list(manifests), sort_keys=False, default_flow_style=False)