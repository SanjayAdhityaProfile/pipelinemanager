from sqlalchemy import select, insert, update
from models import deployments
import yaml
import json
from pathlib import Path
from services.namespace_services import get_namespace_by_id
from services.blobstorage_services import upload_blob_to_azure
from services.cluster_services import get_cluster_by_id
from services.sa_services import get_service_accounts_in_namespace


def get_deployments_by_namespace(conn, namespace_id: int):
    """
    Retrieve all deployments for a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to fetch the deployments for.

    Returns:
        A list of deployments for the specified namespace.
    """
    try:
        # Select deployments where the namespace_id matches
        stmt = select(deployments.c.id,
                      deployments.c.namespace_id,
                      deployments.c.application_name,
                      deployments.c.limit_cpu,
                      deployments.c.limit_memory,
                      deployments.c.request_cpu,
                      deployments.c.request_memory,
                      deployments.c.container_port,
                      deployments.c.config_map_name,
                      deployments.c.seperate_cofig,
                      deployments.c.managed_indentity
                      ).where(
            deployments.c.namespace_id == namespace_id)
        result = conn.execute(stmt).fetchall()
        # return result
        # column_names = result.keys() if result else []
        # Return deployments as a list of dictionaries
        adta = []
        for deployment in result:
            print(deployment)
            adta.append({
                            "id": deployment[0],
                            "namespace_id": deployment[1],
                            "application_name": deployment[2],
                            "limit_cpu": deployment[3],
                            "limit_memory": deployment[4],
                            "request_cpu": deployment[5],
                            "request_memory": deployment[6],
                            "container_port": deployment[7],
                            "config_map_name": deployment[8],
                            "seperate_config": deployment[9],
                            "managed_identity": deployment[10]
                        })
        return adta
    except Exception as e:
        return {"error": str(e)}


def get_single_deployment_by_namespace(conn, namespace_id: int, deplyment_id: int):
    """
    Retrieve all deployments for a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to fetch the deployments for.

    Returns:
        A list of deployments for the specified namespace.
    """
    try:
        # Select deployments where the namespace_id matches
        stmt = select(deployments).where(
            (deployments.c.namespace_id == namespace_id) &
            (deployments.c.id == deplyment_id)
        )

        result = conn.execute(stmt).fetchall()
        # Return deployments as a list of dictionaries
        return [
            {
                "id": deployment[0],
                "namespace_id": deployment[1],
                "application_name": deployment[2],
                "description": deployment[3],
                "image": deployment[4],
                "limit_cpu": deployment[5],
                "limit_memory": deployment[6],
                "request_cpu": deployment[7],
                "request_memory": deployment[8],
                "replica_number": deployment[9],
                "container_port": deployment[10],
                "target_port": deployment[10],
                "seperate_config": deployment[15],
                "managed_identity": deployment[16]
            }
            for deployment in result
        ]
    except Exception as e:
        return {"error": str(e)}


def add_deployment_to_namespace(conn, namespace_id: int, deployment_data: dict):
    """
    Add a deployment to a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to add the deployment to.
        deployment_data: A dictionary containing deployment details such as:
            - application_name
            - description
            - image
            - limit_cpu
            - limit_memory
            - request_cpu
            - request_memory
            - replica_number
            - container_port
            - config_map_name

    Returns:
        A dictionary containing the newly added deployment's details.
    """
    try:
        namespace_name = get_namespace_by_id(namespace_id)
        # Prepare the data for the new deployment
        new_deployment = {
            "namespace_id": namespace_id,
            "application_name": deployment_data["application_name"]+"-"+namespace_name[1],
            "description": deployment_data["application_name"],
            "image": deployment_data["application_name"]+"-"+namespace_name[1],
            "limit_cpu": deployment_data["limit_cpu"],
            "limit_memory": deployment_data["limit_memory"],
            "request_cpu": deployment_data["request_cpu"],
            "request_memory": deployment_data["request_memory"],
            "replica_count": deployment_data["replica_count"],
            "container_port": deployment_data["container_port"],
            "config_map_name": namespace_name[1]+"-config",
            "replica_number": None,
            "seperate_cofig": deployment_data["seperate_cofig"],
            "managed_identity": deployment_data["managed_identity"]
        }
        # Insert the new deployment into the database
        stmt = insert(deployments).values(new_deployment)

        conn.execute(stmt)
        conn.commit()
        if deployment_data["managed_identity"] == 'True':
            print("Managed Identity is enabled for this deployment.")
            managed_identity = namespace_name[1]+"-managed-identity"

        # Fetch and return the newly created deployment details
        stmt_select = select(deployments).where(
            deployments.c.namespace_id == namespace_id
        ).order_by(
            deployments.c.created_at.desc()
        ).limit(1)
        result = conn.execute(stmt_select).fetchone()
        return {
            "id": result.id,
            "namespace_id": result.namespace_id,
            "application_name": result.application_name,
            "description": result.description,
            "image": result.image,
            "limit_cpu": result.limit_cpu,
            "limit_memory": result.limit_memory,
            "request_cpu": result.request_cpu,
            "request_memory": result.request_memory,
            "replica_count": result.replica_count,
            "container_port": result.container_port,
            "config_map_name": result.config_map_name,
            "seperate_config": result.seperate_cofig,
            "managed_identity": result.managed_identity,
            "created_at": result.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {"error": str(e)}


def update_deployment(conn, namespace_id: int, dep_id: int, deployment_data: dict):
    """
    Update a deployment for a specific namespace and application name.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace.
        application_name: The name of the application whose deployment is to be updated.
        deployment_data: A dictionary containing the updated deployment details.

    Returns:
        A dictionary containing the updated deployment's details or an error message.
    """
    try:
        # Prepare the update statement
        stmt = (
            update(deployments)
            .where(
                (deployments.c.namespace_id == namespace_id)
                & (deployments.c.id == dep_id)
            )
            .values(
                limit_cpu=deployment_data.get("limit_cpu"),
                limit_memory=deployment_data.get("limit_memory"),
                request_cpu=deployment_data.get("request_cpu"),
                request_memory=deployment_data.get("request_memory"),
                replica_count=1,
                container_port=deployment_data.get("container_port"),
                seperate_cofig=deployment_data.get("seperate_config"),
                managed_identity=deployment_data.get("managed_identity")
            )
        )
        # Execute the update statement
        result = conn.execute(stmt)
        conn.commit()

        if result.rowcount == 0:
            # If no rows were affected, return an error
            return {"error": "Deployment not found or no changes were made"}
        else:
            # Fetch the updated row in a separate query
            fetch_stmt = (
                select(deployments)
                .where(
                    (deployments.c.namespace_id == namespace_id)
                    & (deployments.c.id == dep_id)
                )
            )
            updated_row = conn.execute(fetch_stmt).fetchone()

            if updated_row:
                # Return the updated deployment details
                return {
                    "id": updated_row.id,
                    "namespace_id": updated_row.namespace_id,
                    "application_name": updated_row.application_name,
                    "description": updated_row.description,
                    "image": updated_row.image,
                    "limit_cpu": updated_row.limit_cpu,
                    "limit_memory": updated_row.limit_memory,
                    "request_cpu": updated_row.request_cpu,
                    "request_memory": updated_row.request_memory,
                    "replica_number": updated_row.replica_number,
                    "container_port": updated_row.container_port,
                    "config_map_name": updated_row.config_map_name,
                    "seperate_config": updated_row.seperate_cofig,
                    "managed_identity": updated_row.managed_identity,
                    "created_at": updated_row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            else:
                # This case should not occur unless the row is deleted before fetch
                return {"error": "Failed to fetch updated deployment details"}

    except Exception as e:
        return {"error": str(e)}


def create_single_deployment_yaml(conn, namespace_id: int, deployment_id: int, file_path: str = None) -> dict:
    """
    Generate a deployment YAML file for a given namespace and deployment name.

    Args:
        conn: Database connection.
        namespace_name: The name of the namespace.
        deployment_name: The name of the deployment.
        file_path: Optional file path where the deployment.yaml will be saved. Defaults to None, which saves in the current directory.

    Returns:
        A dictionary indicating success or error.
    """
    try:
        # Fetch namespace details from the database
        namespace = get_namespace_by_id(namespace_id=namespace_id)
        if not namespace:
            return {"error": "Namespace not found."}
        namespace_name = namespace[1]
        # Fetch deployment details for the given namespace and deployment name
        stmt_deployment = select(deployments).where(
            (deployments.c.namespace_id == namespace_id) &
            (deployments.c.id == deployment_id)
        )
        deployment = conn.execute(stmt_deployment).fetchone()
        cluster = get_cluster_by_id(namespace[2])
        if not deployment:
            return {"error": "Deployment not found for the given namespace and deployment name."}
        print(namespace)

        if namespace[5] != None and namespace[6] != "No nodeselector":
            teleration_data = namespace[7]
            nodeselector_data = namespace[6]
        else: 
            teleration_data = cluster[5]
            nodeselector_data = cluster[6]

        configs = [
            {
                "configMapRef": {
                    "name": f"{namespace_name}-config"
                }
            }
        ]
        if 'True' == deployment[15]:
            configs.append(
                {
                    "configMapRef": {
                        "name": f"{deployment[2]}-config"
                    }
                }
            )
                # Prepare the deployment YAML data
        deployment_yaml = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",                       
            "metadata": {
                "name": deployment[2],
                "namespace": namespace_name
            },
            "spec": {
                "replicas": deployment[5],
                "selector": {
                    "matchLabels": {
                        "app": deployment[2]
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": deployment[2]
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": deployment[2],
                                "image": f"containerrepo/{deployment[2]}:tag",
                                "ports": [
                                    {"containerPort":
                                     deployment[7]}
                                ],
                                "resources": {
                                    "limits": {
                                        "cpu": deployment[8],
                                        "memory": deployment[9]
                                    },
                                    "requests": {
                                        "cpu": deployment[11],
                                        "memory": deployment[12]
                                    }
                                },
                                "envFrom": configs
                            }
                        ]
                    }
                }
            }
        }

        # Conditionally add managed identity if enabled
        if 'True' == deployment[16]:
            print("Managed Identity is enabled for this deployment.")
            deployment_yaml["spec"]["template"]["metadata"]["labels"]["azure.workload.identity/use"]  = "true"
            deployment_yaml["spec"]["template"]["spec"]["serviceAccountName"] = get_service_accounts_in_namespace(conn, namespace_id)

        # Conditionally add tolerations
        if str(teleration_data).lower() != 'null':
            deployment_yaml["spec"]["template"]["spec"]["tolerations"] = json.loads(teleration_data)

        # Conditionally add nodeSelector
        if str(nodeselector_data).lower() != 'null':
            deployment_yaml["spec"]["template"]["spec"]["nodeSelector"] = json.loads(nodeselector_data)

        if not file_path:
            file_path = f"{namespace_name}/deployment/{deployment.application_name}-deployment.yaml"

        # Ensure the directories exist
        output_path = Path(file_path)
        # Create parent directories if not exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the data to a YAML file
        with open(output_path, "w") as yaml_file:
            yaml.dump(deployment_yaml, yaml_file, default_flow_style=False)

        result = upload_blob_to_azure(file_path, file_path)
        # create_deployment_configmap_yaml(conn,namespace_id, deployment_id)
        # create_single_service_yaml(conn, namespace_id, deployment_id)
        return {"message": f"Deployment map YAML file '{output_path}' created successfully.", "uploaded to storage account": str(result)}
    except Exception as e:
        return {"error": str(e)}
