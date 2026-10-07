from fastapi import FastAPI, HTTPException, APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from services.cluster_services import *
from services.branches_services import *
from services.config_services import *
from services.deployment_services import *
from services.namespace_services import *
from services.project_services import *
from services.repo_services import *
from services.service_services import *
from services.user_services import *
from services.pipeline_services import *
from services.logics import *
from services.dep_config_services import *
from routes.auth_routes import auth_router
from routes.user_routes import user_router

app = FastAPI()
  
cluster_router = APIRouter()
project_router = APIRouter()
repository_router = APIRouter()
branch_router = APIRouter()
namespace_router = APIRouter()
configmap_router = APIRouter()
deployment_router = APIRouter()
service_router = APIRouter()
dep_config_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add your React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


class ReqNamespace(BaseModel):
    name: str
    registry: str
    cluster_id: int


class ResNamespace(BaseModel):
    id: int
    name: str


class ReqUserSubscription(BaseModel):
    user_id: int
    namespace_id: int

# Pydantic models for config data


class ReqConfig(BaseModel):
    config_key: str
    config_value: str
    description: str = None  # Optional description field


class EditReqConfig(BaseModel):
    config_key: str
    config_value: str
    description: str = None  # Optional description field
    namespace_id: int

class ResConfig(BaseModel):
    id: int
    config_key: str
    config_value: str
    description: str = None


class ResDepConfig(BaseModel):
    id: int
    config_key: str
    config_value: str
    description: str = None
    created_at: str


class ReqDeployment(BaseModel):
    application_name: str
    limit_cpu: str
    limit_memory: str
    request_cpu: str
    request_memory: str
    replica_count: int
    container_port: int
    seperate_cofig: str = 'False'
    managed_identity: str | None = None  # Optional field for managed identity


class upReqDeployment(BaseModel):
    limit_cpu: str
    limit_memory: str
    request_cpu: str
    request_memory: str
    container_port: int
    seperate_config: str
    managed_identity: str | None = None  # Optional field for managed identity


class inputToDeployment(BaseModel):
    application_name: str


class ResDeployment(BaseModel):
    id: int
    application_name: str
    description: str | None
    image: str | None
    limit_cpu: str
    limit_memory: str
    request_cpu: str
    request_memory: str
    replica_number: int
    container_port: int
    managed_identity: str | None = None  # Optional field for managed identity
# Pydantic model for the service data


class ServiceData(BaseModel):
    port: int


@repository_router.post("/")
def registry_by_namespace(deployment_name: List[inputToDeployment]):
    try:
        return get_repository_by_deploymentname(deployment_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")


@cluster_router.get('/get_cluster_project_repo_branch/')
def get_cluster_project_repo_branch(project_name, repo_name, branch_name):
    try:
        return get_cluster_and_namespace(project_name, repo_name, branch_name)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")


@namespace_router.get("/{username}")
def get_namespaces_with_user(username):
    """
    Get all namespaces.
    
    Returns:
        - List of all namespaces
    """
    try:
        namespaces_list = get_all_namespaces_user(username)
        
        if namespaces_list is None:
            raise HTTPException(
                status_code=500, detail="Error fetching namespaces")
        
        # Convert SQLAlchemy rows to dictionaries
        formatted_namespaces = [
            {
                "id": namespace['id'],
                "name": namespace['name'],
                # "cluster_id": namespace.cluster_id,
                # "registry": namespace.registry if hasattr(namespace, 'registry') else None,
                # "created_at": str(namespace.created_at) if hasattr(namespace, 'created_at') and namespace.created_at else None,
                # "updated_at": str(namespace.updated_at) if hasattr(namespace, 'updated_at') and namespace.updated_at else None
            }
            for namespace in namespaces_list
        ]
        
        return {
            "status": "success",
            "count": len(formatted_namespaces),
            "namespaces": formatted_namespaces
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching namespaces: {str(e)}")

@namespace_router.get("/")
def get_namespaces():
    """
    Get all namespaces.
    
    Returns:
        - List of all namespaces
    """
    try:
        namespaces_list = get_all_namespaces()
        
        if namespaces_list is None:
            raise HTTPException(
                status_code=500, detail="Error fetching namespaces")
        
        # Convert SQLAlchemy rows to dictionaries
        formatted_namespaces = [
            {
                "id": namespace[0],
                "name": namespace[1],
                # "cluster_id": namespace['cluster_id'],
                # "registry": namespace['registry'] if 'registry' in namespace else None,
                # "created_at": str(namespace['created_at']) if 'created_at' in namespace and namespace['created_at'] else None,
                # "updated_at": str(namespace['updated_at']) if 'updated_at' in namespace and namespace['updated_at'] else None
            }
            for namespace in namespaces_list
        ]
        
        return {
            "status": "success",
            "count": len(formatted_namespaces),
            "namespaces": formatted_namespaces
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching namespaces: {str(e)}")


@namespace_router.post("/")
def create_namespace(namespaces: List[ReqNamespace]):
    try:
        return create_namespaces([{"name": namespace.name, "registry": namespace.registry, "cluster_id": namespace.cluster_id} for namespace in namespaces])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")
    
@namespace_router.post("/")
def create_namespace_yaml(namespaces: List[ReqNamespace]):
    try:
        result = []
        with engine.connect() as conn:
            for namespace in namespaces:
              result.append(generate_namespace_yaml(conn, namespace_id=namespace.id))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")

@namespace_router.delete("/{namespace_id}")
def delete_namespace(namespace_id: int):
    try:
        return delete_namespace_by_id(namespace_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating namespaces: {str(e)}")


@namespace_router.post("/subscribe")
def subscribe_user_to_namespace(subscription: ReqUserSubscription):
    """
    Subscribe a user to a namespace.
    
    Request Body:
        - user_id: The ID of the user
        - namespace_id: The ID of the namespace
        
    Returns:
        - Success message with subscription details
    """
    try:
        result = add_user_subscription(subscription.user_id, subscription.namespace_id)
        
        if result is None:
            raise HTTPException(
                status_code=500, 
                detail="Failed to create subscription"
            )
        
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error creating subscription: {str(e)}"
        )


@namespace_router.get("/subscriptions")
def get_all_subscriptions():
    """
    Get all user-namespace subscriptions.
    
    Returns:
        - List of all subscription records
    """
    try:
        subscriptions = get_all_user_namespace_subscriptions()
        
        if subscriptions is None:
            raise HTTPException(
                status_code=500,
                detail="Error fetching subscriptions"
            )
        
        # Convert SQLAlchemy rows to dictionaries
        formatted_subscriptions = [
            {
                "id": sub.id,
                "user_id": sub.user_id,
                "namespace_id": sub.namespace_id,
                "subscription_date": str(sub.subscription_date) if sub.subscription_date else None
            }
            for sub in subscriptions
        ]
        
        return {
            "status": "success",
            "count": len(formatted_subscriptions),
            "subscriptions": formatted_subscriptions
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching subscriptions: {str(e)}"
        )


@configmap_router.get("/{namespace_id}/configmaps")
def get_config_maps(namespace_id: int):
    try:
        return get_config_maps_by_namespace(namespace_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching config maps: {str(e)}")


@configmap_router.post("/{namespace_id}/configmaps")
def add_config_maps(namespace_id: int, config_data: List[ReqConfig]):
    try:
        sucessFlag = False
        with engine.connect() as conn:
            config = add_configs_to_namespace(conn, namespace_id, [config.dict() for config in config_data])
            if 'error' not in config:
                sucessFlag = True
            if 'error' not in create_configmap_yaml(conn, namespace_id):
                sucessFlag = True
            return {"status": sucessFlag, 'config': config}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding config maps: {str(e)}")


@configmap_router.put("/{namespace_id}/configmaps/{config_key}")
def edit_config_map(namespace_id: int, config_key: str, config_data: EditReqConfig):
    try:
        sucessFlag = False
        print(config_data.namespace_id)
        with engine.connect() as conn:
            updated_config_map = update_config_map(
                conn, namespace_id, config_key, config_data.model_dump())
            if 'error' not in updated_config_map:
                sucessFlag = True
            if 'error' not in create_configmap_yaml(conn, config_data.namespace_id):
                sucessFlag = True
        return {"status": sucessFlag, "upadtedData": updated_config_map}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error editing config map: {str(e)}")


@configmap_router.delete("/{config_id}")
def delete_config_map(config_id: int):
    try:
        with engine.connect() as conn:
            deleted_config_map = delete_config_by_id(conn, config_id)
            if not deleted_config_map:
                raise HTTPException(
                    status_code=404, detail="Config map not found or namespace not found")
            return deleted_config_map
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error editing config map: {str(e)}")


@configmap_router.patch("/{namespace_id}/generate_configmaps")
def generate_config_map_yaml(namespace_id: int):
    try:
        with engine.connect() as conn:
            return create_configmap_yaml(conn, namespace_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error editing config map: {str(e)}")


@deployment_router.get("/{namespace_id}/deployments")
def get_deployments(namespace_id: int):
    try:
        with engine.connect() as conn:
            deployments = get_deployments_by_namespace(conn, namespace_id)
            return deployments
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching config maps: {str(e)}")


@deployment_router.get("/{namespace_id}/deployments/{deployment_id}")
def get_deployment_by_id(namespace_id: int, deployment_id: int):
    try:
        with engine.connect() as conn:
            deployments = get_single_deployment_by_namespace(
                conn, namespace_id, deployment_id)
            return deployments
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching config maps: {str(e)}")


@deployment_router.put("/{namespace_id}/deployment_id/{deployment_id}")
def update_deployment_to_namespace_route(namespace_id: int, deployment_id: int, deployment_data: upReqDeployment):
    try:
        with engine.connect() as conn:
            # Add the deployment to the namespace and Return the created deployment details
            new_dep_id = update_deployment(
                conn, namespace_id, deployment_id, deployment_data.dict())

            res_service = update_service_to_deployments_by_namespace(conn, new_dep_id["namespace_id"], new_dep_id["id"], new_dep_id["application_name"], {
                                                                     "description": new_dep_id["description"], "port": new_dep_id["container_port"]})
            result_ = create_single_deployment_yaml(
                conn, namespace_id, new_dep_id['id']
            )

            result = create_single_service_yaml(
                conn, namespace_id, new_dep_id['id']
            )

            return {
                "result_deployment": result_,
                "result_service": result
            }
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail=f"Error adding deployment: {str(e)}")


@deployment_router.post("/{namespace_id}/deployments")
def add_deployment_to_namespace_route(namespace_id: int, deployment_data: ReqDeployment):
    try:
        with engine.connect() as conn:
            # Fetch the namespace's config map name from the namespace specification
            namespace_spec = get_namespace_by_id(namespace_id)

            if not namespace_spec:
                raise HTTPException(
                    status_code=404, detail="Namespace not found or no config map defined")

            config_map_name = namespace_spec[1]+'-config'

            # Add the config_map_name to the deployment data
            deployment_data_dict = deployment_data.dict()
            deployment_data_dict['config_map_name'] = config_map_name

            # Add the deployment to the namespace and Return the created deployment details
            new_dep_id = add_deployment_to_namespace(
                conn, namespace_id, deployment_data_dict)


            
            create_single_deployment_yaml(
                conn, namespace_id, new_dep_id['id'])
            add_service_to_deployments_by_namespace(
                conn, namespace_id, new_dep_id['id']
            )
            result = create_single_service_yaml(
                conn, namespace_id, new_dep_id['id']
            )

            return {
                "result_service": result
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding deployment: {str(e)}")


@app.get('/')
def infra_check():
    return HTTPException(status_code=200)


@deployment_router.post("/{namespace_id}/generate_deployment/{deployment_id}")
def create_deployment_yaml(namespace_id: int, deployment_id: int):
    try:
        with engine.connect() as conn:
            return {
                "deployment_yaml": create_single_deployment_yaml(conn, namespace_id, deployment_id),
                "service_yaml": create_single_service_yaml(conn, namespace_id, deployment_id)
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error editing config map: {str(e)}")


@service_router.get("/{namespace_id}/deployments/{deployment_id}/services")
def get_services_by_deployment_namespace(namespace_id: int, deployment_id: int):
    """
    Retrieve all services for a specific deployment within a specific namespace.

    Args:
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.

    Returns:
        A list of services for the specified deployment and namespace or an error message.
    """
    try:
        with engine.connect() as conn:
            # Call the function to fetch services
            return get_service_by_deployments_by_namespace(conn, namespace_id, deployment_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching services: {str(e)}")


@service_router.post("/{namespace_id}/deployments/{deployment_id}/services")
def add_service_to_deployment_namespace(
    namespace_id: int,
    deployment_id: int
):
    """
    Add a service to a specific deployment within a namespace.

    Args:
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.
        service_data: The details of the service to be added.

    Returns:
        The details of the newly added service or an error message.
    """
    try:
        with engine.connect() as conn:
            # Call the service function
            result = add_service_to_deployments_by_namespace(
                conn, namespace_id, deployment_id
            )

            # Handle errors returned by the function
            if isinstance(result, dict) and "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding service: {str(e)}")


@service_router.get("/{namespace_id}/deployments/{deployment_id}")
def generate_service_to_deployment_namespace(
        namespace_id: int,
        deployment_id: int):
    """
    Create a service yaml for a specific deployment and namespace.

    Args:
        namespace_id: The ID of the namespace.
        deployment_id: The ID of the deployment.
        service_name: The name of the service to be updated.
        service_data: The updated details of the service.

    Returns:
        The updated service's details or an error message.
    """
    try:
        with engine.connect() as conn:

            # Call the service function
            result = create_single_service_yaml(
                conn, namespace_id, deployment_id
            )

            # Handle errors returned by the function
            if isinstance(result, dict) and "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating service: {str(e)}")


@dep_config_router.get("/{deployment_id}/depconfig")
def get_deploy_config(deployment_id: int):
    try:
        with engine.connect() as conn:
            return get_config_by_deployment(conn, deployment_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching config maps: {str(e)}")


@dep_config_router.post("/{namespace_id}/{deployment_id}/depconfig")
def add_config_maps(namespace_id: int, deployment_id: int, config_data: List[ReqConfig]):
    try:
        sucessFlag = False
        with engine.connect() as conn:
            if 'error' not in add_config_to_deployment(conn, deployment_id, [config.dict() for config in config_data]):
                sucessFlag = True
            if 'error' not in create_deployment_configmap_yaml(conn, namespace_id, deployment_id):
                sucessFlag = True
            return {"status": sucessFlag}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding config maps: {str(e)}")


@dep_config_router.put("/{namespace_id}/{deployment_id}/depconfig/{config_id}")
def update_config_maps(namespace_id: int, deployment_id: int, config_id: int, config_data: List[ReqConfig]):
    try:
        sucessFlag = False
        with engine.connect() as conn:
            if 'error' not in update_config_to_deployment(conn, deployment_id, config_id, [config.dict() for config in config_data]):
                sucessFlag = True
            if 'error' not in create_deployment_configmap_yaml(conn, namespace_id, deployment_id):
                sucessFlag = True
            return {"status": sucessFlag}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding config maps: {str(e)}")


@dep_config_router.delete("/{namespace_id}/{deployment_id}/depconfig/{config_id}")
def delete_config_maps(namespace_id: int, deployment_id: int, config_id: int):

    try:
        sucessFlag = False
        with engine.connect() as conn:
            if 'error' not in delete_config_of_deployment(conn, deployment_id, config_id):
                sucessFlag = True
            if 'error' not in create_deployment_configmap_yaml(conn, namespace_id, deployment_id):
                sucessFlag = True
            return {"status": sucessFlag}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding config maps: {str(e)}")

# Include the namespace_router and configmap_router in the app
app.include_router(auth_router)  # Authentication routes
app.include_router(user_router)  # User management routes
app.include_router(cluster_router, prefix="/cluster", tags=["Cluster"])
app.include_router(project_router, prefix="/project", tags=["Project"])
app.include_router(repository_router, prefix="/repo", tags=["Repository"])
app.include_router(branch_router, prefix="/branch", tags=["Branch"])
app.include_router(namespace_router, prefix="/namespaces", tags=["Namespace"])
app.include_router(configmap_router, prefix="/configmap", tags=["ConfigMap"])
app.include_router(deployment_router, prefix="/deployments",
                   tags=["Deployment"])
app.include_router(service_router, prefix="/services", tags=["Service"])
app.include_router(dep_config_router,
                   prefix="/dep_config_router", tags=["Dep_config_router"])
