from sqlalchemy import select, insert, update
from models import deployments, services

import yaml
from pathlib import Path
from services.namespace_services import get_namespace_by_id
from services.blobstorage_services import upload_blob_to_azure


def get_service_by_deployments_by_namespace(conn, namespace_id: int, deployment_id: int):
    """
    Retrieve all services for a specific deployment within a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to fetch the services for.
        deployment_id: The ID of the deployment to fetch the services for.

    Returns:
        A list of services for the specified deployment and namespace.
    """
    try:
        # Check if the deployment exists in the given namespace
        deployment_stmt = select(deployments).where(
            (deployments.c.id == deployment_id) &
            (deployments.c.namespace_id == namespace_id)
        )
        deployment = conn.execute(deployment_stmt).fetchone()

        if not deployment:
            return {"error": "Deployment does not exist in the specified namespace."}

        # Fetch services for the deployment
        services_stmt = select(services).where(
            services.c.deployment_id == deployment_id)
        result = conn.execute(services_stmt).fetchall()

        # Return services as a list of dictionaries
        return [
            {
                "id": service.id,
                "deployment_id": service.deployment_id,
                "application_name": service.application_name,
                "service_name": service.service_name,
                "description": service.description,
                "port": service.port,
                "target_port": service.port,
                "created_at": service.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for service in result
        ]
    except Exception as e:
        return {"error": str(e)}


def add_service_to_deployments_by_namespace(conn, namespace_id: int, deployment_id: int):
    """
    Add a service to a specific deployment within a namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.
        service_data: A dictionary containing service details:
            - application_name
            - service_name
            - description
            - port
            - target_port

    Returns:
        A dictionary containing the newly added service's details or an error message.
    """
    try:
        # Check if the deployment exists in the given namespace
        deployment_stmt = select(deployments).where(
            (deployments.c.id == deployment_id) &
            (deployments.c.namespace_id == namespace_id)
        )
        deployment = conn.execute(deployment_stmt).fetchone()
        if not deployment:
            return {"error": "Deployment does not exist in the specified namespace."}

        # Insert the new service into the database
        new_service = {
            "deployment_id": deployment_id,
            "application_name": deployment[2],
            "service_name": deployment[2],
            "description":  None,
            "port": deployment[7],
            "target_port": deployment[7],
        }
        stmt = insert(services).values(new_service)
        conn.execute(stmt)
        conn.commit()

        # Fetch and return the newly created service details
        stmt_select = select(services).where(services.c.deployment_id == deployment_id).order_by(
            services.c.created_at.desc()
        ).limit(1)
        result = conn.execute(stmt_select).fetchone()

        return {
            "id": result.id,
            "deployment_id": result.deployment_id,
            "application_name": result.application_name,
            "service_name": result.service_name,
            "description": result.description,
            "port": result.port,
            "target_port": result.target_port,
            "created_at": result.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        return {"error": str(e)}


def update_service_to_deployments_by_namespace(conn, namespace_id: int, deployment_id: int, service_name: str, service_data: dict):
    """
    Update a service for a specific deployment and namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.
        service_name: The name of the service to be updated.
        service_data: A dictionary containing the updated service details.

    Returns:
        A dictionary containing the updated service's details or an error message.
    """
    try:
        # Check if the deployment exists in the given namespace
        deployment_stmt = select(deployments).where(
            (deployments.c.id == deployment_id) &
            (deployments.c.namespace_id == namespace_id)
        )

        deployment = conn.execute(deployment_stmt).fetchone()

        if not deployment:
            return {"error": "Deployment does not exist in the specified namespace."}

        # Update the service in the database
        stmt = (
            update(services)
            .where(
                (services.c.deployment_id == deployment_id) &
                (services.c.service_name == service_name)
            )
            .values(
                description=service_data.get("description"),
                target_port=service_data.get("port"),
                port=service_data.get("port"),
            )
        )
        result = conn.execute(stmt)
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Service not found or no changes were made."}

        # Fetch and return the updated service details
        stmt_select = select(services).where(
            (services.c.deployment_id == deployment_id) &
            (services.c.service_name == service_name)
        )
        updated_row = conn.execute(stmt_select).fetchone()

        return {
            "id": updated_row.id,
            "deployment_id": updated_row.deployment_id,
            "application_name": updated_row.application_name,
            "service_name": updated_row.service_name,
            "description": updated_row.description,
            "port": updated_row.target_port,
            "target_port": updated_row.target_port,
            "created_at": updated_row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        print(e)
        return {"error": str(e)}


def create_single_service_yaml(conn, namespace_id: int, deployment_id: int, file_path: str = None):
    """
    Generate a service YAML file for a given namespace, deployment, and service.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.
        service_name: The name of the service.
        file_path: Optional file path where the service.yaml will be saved.

    Returns:
        A dictionary indicating success or error.
    """
    try:

        # get namespace data
        namespace_name = get_namespace_by_id(namespace_id=namespace_id)

        if not namespace_name:
            return {"error": "Namespace not found."}

        # Fetch deployment and namespace details
        deployment_stmt = select(deployments).where(
            (deployments.c.id == deployment_id) &
            (deployments.c.namespace_id == namespace_id)
        )
        deployment = conn.execute(deployment_stmt).fetchone()
        if not deployment:
            return {"error": "Deployment does not exist in the specified namespace."}

        # Fetch service details
        service_stmt = select(services).where(
            (services.c.deployment_id == deployment_id) &
            (services.c.service_name == deployment[2])
        )
        service = conn.execute(service_stmt).fetchone()
        if not service:
            return {"error": "Service not found for the specified deployment."}

        # Prepare the service YAML data
        service_yaml = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": deployment.application_name+"-"+"service",
                "namespace": namespace_name[1]
            },
            "spec": {
                "selector": {
                    "app": deployment[2]
                },
                "ports": [
                    {
                        "port": service[4],
                        "targetPort": service[5]
                    }
                ]
            }
        }

        # Define the file path
        if not file_path:
            file_path = f"{namespace_name[1]}/service/{deployment[2]}-service.yaml"

        # Ensure the directories exist
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data to a YAML file
        with open(output_path, "w") as yaml_file:
            yaml.dump(service_yaml, yaml_file, default_flow_style=False)

        result = upload_blob_to_azure(file_path, file_path)

        return {"message": f"Deployment map YAML file '{output_path}' created successfully.", "uploaded to storage account": str(result)}
    except Exception as e:
        return {"error": str(e)}
