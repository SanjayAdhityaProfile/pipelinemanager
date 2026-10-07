from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
from models import Dep_config, namespaces, engine
from pathlib import Path
from services.blobstorage_services import upload_blob_to_azure
from services.deployment_services import get_single_deployment_by_namespace
import yaml


class DoubleQuotedStr(str):
    """Custom string type to enforce double quotes in YAML output."""
    pass


def double_quoted_representer(dumper, data):
    """YAML representer to handle double-quoted strings."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


# Register the custom representer
yaml.add_representer(DoubleQuotedStr, double_quoted_representer)

def get_config_by_deployment(conn, deployment_id: int):
    """
    Retrieve all configurations for a specific deployment.

    Args:
        conn: Database connection.
        deployment_id: The ID of the deployment to fetch the configurations for.

    Returns:
        A list of configurations for the specified deployment.
    """
    try:
        stmt = select(Dep_config).where(
            Dep_config.c.deployment_id == deployment_id)
        result = conn.execute(stmt).fetchall()
        return [
            {
                "id": config.id,
                "deployment_id": config.deployment_id,
                "config_key": config.config_key,
                "config_value": config.config_value,
                "description": config.description,
                "created_at": config.created_at,
                "updated_at": config.updated_at,
            }
            for config in result
        ]
    except SQLAlchemyError as e:
        return {"error": str(e)}


def get_single_config(conn, config_id: int):
    """
    Retrieve a single configuration by ID.

    Args:
        conn: Database connection.
        config_id: The ID of the configuration to fetch.

    Returns:
        A dictionary representing the configuration details.
    """
    try:
        stmt = select(Dep_config).where(Dep_config.c.id == config_id)
        result = conn.execute(stmt).fetchone()
        if result:
            return {
                "id": result.id,
                "deployment_id": result.deployment_id,
                "config_key": result.config_key,
                "config_value": result.config_value,
                "description": result.description,
                "created_at": result.created_at,
                "updated_at": result.updated_at,
            }
        return {"error": "Configuration not found"}
    except SQLAlchemyError as e:
        return {"error": str(e)}


def add_config_to_deployment(conn, deployment_id: int, config_data: dict):
    """
    Add a new configuration to a specific deployment.

    Args:
        conn: Database connection.
        deployment_id: The ID of the deployment to add the configuration to.
        config_data: A dictionary containing the configuration details.

    Returns:
        A dictionary with the newly created configuration details.
    """
    try:
        for config in config_data:
            new_config = {
                "deployment_id": deployment_id,
                "config_key": config["config_key"],
                "config_value": config["config_value"],
                "description": config.get("description", ""),
            }
            stmt = insert(Dep_config).values(new_config)
            conn.execute(stmt)
            conn.commit()
        return {"message": "Configuration added successfully"}
    except SQLAlchemyError as e:
        return {"error": str(e)}


def update_config_to_deployment(conn, deployment_id: int, config_id: int, config_data: dict):
    """
    Update a configuration by ID.

    Args:
        conn: Database connection.
        config_id: The ID of the configuration to update.
        config_data: A dictionary containing the updated configuration details.

    Returns:
        A dictionary with the updated configuration details.
    """
    try:
        for config in config_data:
            stmt = (
                update(Dep_config)
                .where(Dep_config.c.id == config_id)
                .where(Dep_config.c.deployment_id == deployment_id)
                .values(
                    config_key=config.get("config_key"),
                    config_value=config.get("config_value"),
                    description=config.get("description", ""),
                )
            )
            result = conn.execute(stmt)
            conn.commit()
        if result.rowcount == 0:
            return {"error": "Configuration not found or no changes made"}
        return {"message": "Configuration updated successfully"}
    except SQLAlchemyError as e:
        return {"error": str(e)}


def delete_config_of_deployment(conn,  deployment_id: int, config_id: int):
    """
    Delete a configuration by ID.

    Args:
        conn: Database connection.
        config_id: The ID of the configuration to delete.

    Returns:
        A success or error message.
    """
    try:
        stmt = delete(Dep_config).where(Dep_config.c.id ==
                                        config_id, Dep_config.c.deployment_id == deployment_id)
        result = conn.execute(stmt)
        conn.commit()
        if result.rowcount == 0:
            return {"error": "Configuration not found"}
        return {"message": "Configuration deleted successfully"}
    except SQLAlchemyError as e:
        return {"error": str(e)}


def create_deployment_configmap_yaml(conn, namespace_id: int, deployment_id: int, file_path: str = None) -> dict:
    """
    Generate a config map YAML file for a given namespace and save it in the desired folder structure.

    Args:
        conn: Database connection.
        deployment_id: The ID of the namespace for which the config map should be generated.
        file_path: Optional file path where the configmap.yaml will be saved. Defaults to None, which saves in the current directory.

    Returns:
        A dictionary indicating success or error.
    """
    try:
        # Fetch namespace name from the database
        stmt = select(namespaces.c.name).where(namespaces.c.id == namespace_id)
        namespace = conn.execute(stmt).fetchone()

        if not namespace:
            return {"error": "Namespace not found."}

        project_name = namespace[0]  # Namespace name
        # Fetch config maps for the given namespace
        config_maps = get_config_by_deployment(conn, deployment_id)
        deployment = get_single_deployment_by_namespace(
            conn, namespace_id, deployment_id)
        deployment = deployment[0]
        deployment_name = deployment['application_name']
        if not config_maps:
            return {"error": "No config maps found for the given namespace."}
        # Prepare the config map data for YAML
        config_map_data = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{deployment_name}-config",
                "namespace": project_name
            },
            "data": {}
        }
        # Populate the 'data' section with config_key and config_value
        for config_map in config_maps:
            config_map_data["data"][config_map["config_key"]
                                    ] = DoubleQuotedStr(config_map["config_value"])
        # Define the file path with the folder structure: namespace/configmap/filename.yaml
        if not file_path:
            file_path = f"{project_name}/deploymentConfigmap/{deployment_name}-config.yaml"
        # # Ensure the directories exist
        output_path = Path(file_path)
        # # Create parent directories if not exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data to a YAML file
        with open(output_path, "w") as yaml_file:
            yaml.dump(config_map_data, yaml_file, default_flow_style=False)

        result = upload_blob_to_azure(file_path, file_path)

        return {"message": f"Config map YAML file '{output_path}' created successfully.", "uploaded to storage account": str(result)}

    except Exception as e:
        return {"error": str(e)}
