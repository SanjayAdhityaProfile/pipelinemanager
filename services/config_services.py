from sqlalchemy import select, insert
from models import namespaces, config_maps
from typing import List, Dict
import yaml
from pathlib import Path
from services.blobstorage_services import upload_blob_to_azure
from fastapi import HTTPException
from models import namespaces, engine
from sqlalchemy.exc import SQLAlchemyError
import logging
logger = logging.getLogger(__name__)

# Create a single or multiple namespaces


def create_namespaces(namespaces_data: List[dict]):
    """
    Create one or multiple namespaces in the database.

    Args:
        conn: Database connection.
        namespaces_data: A list of dictionaries containing namespace names.

    Returns:
        A list of created namespaces with their IDs.
    """
    # Prepare the list of namespaces to insert
    try:
        with engine.connect() as conn:
            namespaces_to_insert = []

            for namespace in namespaces_data:
                namespaces_to_insert.append(
                    {
                        "name": namespace["name"],
                        "cluster_id": namespace["cluster_id"],
                        "registry": namespace["registry"]
                    }
                )

            # Perform the insert operation
            stmt = insert(namespaces).values(namespaces_to_insert)
            conn.execute(stmt)
            conn.commit()
            # Fetch and return the created namespaces
            result = conn.execute(select(namespaces).filter(namespaces.c.name.in_(
                [namespace["name"] for namespace in namespaces_data]))).fetchall()
            
            response  = []
            for i in result:
                response.append({
                    "yaml_created": generate_namespace_yaml(conn, i.id),
                    "id": i.id, 
                    "name": i.name})
                
            return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")


def generate_namespace_yaml(conn, namespace_id: int) -> dict:
    """
    Generate a namespace YAML file for a given namespace and save it in the desired folder structure.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace for which the YAML should be generated.
        file_path: Optional file path where the namespace.yaml will be saved. Defaults to None, which saves in the current directory.

    Returns:
        A dictionary indicating success or error.
    """
    try:
        # Fetch namespace name from the database
        stmt = select(namespaces.c.name).where(namespaces.c.id == namespace_id)
        namespace = conn.execute(stmt).fetchone()
        if not namespace:
            return {"error": "Namespace not found."}

        namespace_name = namespace[0]  # Namespace name

        # Prepare the namespace data for YAML
        namespace_data = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace_name
            }
        }

        # Define the file path with the folder structure: namespace/namespace.yaml
        if not file_path:
            file_path = f"{namespace_name}/namespace/namespace.yaml"

        # Ensure the directories exist
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data to a YAML file
        with open(output_path, "w") as yaml_file:
            yaml.dump(namespace_data, yaml_file,
                      default_flow_style=False, sort_keys=False)

        # Upload the file to Azure Blob Storage
        result = upload_blob_to_azure(str(output_path), str(output_path))

        return {"message": f"Namespace YAML file '{output_path}' created successfully.", "uploaded to storage account": str(result)}

    except Exception as e:
        return {"error": str(e)}


def get_config_maps_by_namespace(namespace_id: int) -> List[dict]:
    """
    Retrieve all config maps for a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to fetch the config maps for.

    Returns:
        A list of config maps for the specified namespace.
    """
    try:
        # Select config maps where the namespace_id matches
        with engine.connect() as conn:
            stmt = select(config_maps).where(
                config_maps.c.namespace_id == namespace_id)
            result = conn.execute(stmt).fetchall()

            # Return config maps as a list of dictionaries
            return [{"id": config_map.id, "config_key": config_map.config_key,
                    "config_value": config_map.config_value,
                     "description": config_map.description,
                     "namespace_id": namespace_id
                     #  "created_at": config_map.created_at.strftime("%Y-%m-%d %H:%M:%S")
                     }
                    for config_map in result]
    except Exception as e:
        return {"error": str(e)}


def add_configs_to_namespace(conn, namespace_id: int, config_data: List[Dict[str, str]]) -> List[dict]:
    """
    Add one or more config entries to a config map for a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to add the config entries to.
        config_data: A list of dictionaries where each dictionary contains
                     'config_key', 'config_value', and optionally 'description'.

    Returns:
        A list of the newly added config maps with their details.
    """
    try:
        # Prepare config entries to insert into the ConfigMaps table
        configs_to_insert = [
            {
                "namespace_id": namespace_id,
                "config_key": config["config_key"],
                "config_value": config["config_value"],
                "description": config.get("description", "")
            }
            for config in config_data
        ]

        # Insert the new configs into the ConfigMaps table
        stmt = insert(config_maps).values(configs_to_insert)
        conn.execute(stmt)
        conn.commit()

        # Fetch and return the newly inserted config maps
        stmt_select = select(config_maps).where(
            config_maps.c.namespace_id == namespace_id).order_by(config_maps.c.created_at.desc())
        result = conn.execute(stmt_select).fetchall()

        return [{"id": config_map.id, "config_key": config_map.config_key,
                 "config_value": config_map.config_value,
                 "description": config_map.description
                 }
                for config_map in result]

    except Exception as e:
        return {"error": str(e)}


def delete_config_by_id(conn, config_id: int) -> dict:
    """
    Delete a specific configuration by its ID.

    Args:
        conn: Database connection.
        config_id: The ID of the configuration to delete.

    Returns:
        A dictionary indicating the success or failure of the operation.
    """
    try:
        # Prepare the delete statement
        delete_stmt = config_maps.delete().where(config_maps.c.id == config_id)

        # Execute the delete statement
        result = conn.execute(delete_stmt)
        conn.commit()

        # Check if any row was deleted
        if result.rowcount == 0:
            return {"status": "error", "message": f"No config found with ID {config_id}."}

        return {"status": "success", "message": "Config deleted successfully."}

    except SQLAlchemyError as e:
        logger.error(f"Error deleting config by ID {config_id}: {e}")
        return {"status": "error", "message": f"Error deleting config: {e}"}

    except Exception as e:
        logger.error(
            f"Unexpected error while deleting config by ID {config_id}: {e}")
        return {"status": "error", "message": f"Unexpected error: {e}"}


def update_config_map(conn, namespace_id: int, config_key: str, new_values: Dict[str, str]) -> dict:
    """
    Update the config value and/or description of a specific config map.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace.
        config_key: The config key to update.
        new_values: A dictionary with keys `config_value` (required) and `description` (optional).

    Returns:
        A dictionary containing the updated config map or an error message.
    """
    try:
        # Validate input
        if "config_value" not in new_values:
            raise ValueError(
                "The 'config_value' key is required in new_values.")

        # Prepare the update statement
        stmt = (
            config_maps.update()
            .where(
                (config_maps.c.id == namespace_id) &
                (config_maps.c.config_key == config_key)
            )
            .values(
                config_value=new_values["config_value"],
                description=new_values.get("description", "")
            )
        )

        # Execute the update statement
        result = conn.execute(stmt)
        conn.commit()

        # Check if any row was updated
        if result.rowcount == 0:
            return {"error": "No config map found for the given namespace ID and config key."}

        # Fetch and return the updated config map
        stmt_select = (
            select(config_maps)
            .where(
                (config_maps.c.id == namespace_id) &
                (config_maps.c.config_key == config_key)
            )
        )
        updated_config = conn.execute(stmt_select).fetchone()
        return {
            "id": updated_config.id,
            "namespace_id": updated_config.namespace_id,
            "config_key": updated_config.config_key,
            "config_value": updated_config.config_value,
            "description": updated_config.description,
            "created_at": updated_config.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": updated_config.updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_config.updated_at else None,
        }

    except Exception as e:
        return {"error": str(e)}


class DoubleQuotedStr(str):
    """Custom string type to enforce double quotes in YAML output."""
    pass


def double_quoted_representer(dumper, data):
    """YAML representer to handle double-quoted strings."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


# Register the custom representer
yaml.add_representer(DoubleQuotedStr, double_quoted_representer)


def create_configmap_yaml(conn, namespace_id: int, file_path: str = None) -> dict:
    """
    Generate a config map YAML file for a given namespace and save it in the desired folder structure.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace for which the config map should be generated.
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
        config_maps = get_config_maps_by_namespace(namespace_id)

        if not config_maps:
            return {"error": "No config maps found for the given namespace."}

        # Prepare the config map data for YAML
        config_map_data = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{project_name}-config",
                "namespace": project_name
            },
            "data": {}
        }
        # Populate the 'data' section with config_key and config_value
        for config_map in config_maps:
            # Use DoubleQuotedStr to enforce double quotes
            config_map_data["data"][config_map["config_key"]
                                    ] = DoubleQuotedStr(config_map["config_value"])

        # Define the file path with the folder structure: namespace/configmap/filename.yaml
        if not file_path:
            file_path = f"{project_name}/configmap/{project_name}-config.yaml"

        # Ensure the directories exist
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data to a YAML file
        with open(output_path, "w") as yaml_file:
            yaml.dump(config_map_data, yaml_file,
                      default_flow_style=False, sort_keys=False)

        # Upload the file to Azure Blob Storage
        result = upload_blob_to_azure(str(output_path), str(output_path))

        return {"message": f"Config map YAML file '{output_path}' created successfully.", "uploaded to storage account": str(result)}

    except Exception as e:
        return {"error": str(e)}
