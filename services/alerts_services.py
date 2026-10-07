import yaml
from pathlib import Path

from services.blobstorage_services import upload_blob_to_azure


# Static defaults for the App Gateway backend-pool unhealthy alert.
# Anything user-specific (namespace, deployment_name, service_port) is injected
# at call time; alert_name and rg_tags.project are derived.
_APPGW_BP_DEFAULTS = {
    "action_group_id": "/subscriptions/2DA7649E-9FD1-4B68-A1B3-B9F4C429580E/resourceGroups/alearts/providers/microsoft.insights/actionGroups/myActionGroup",
    "action_group_name": "myActionGroup",
    "action_group_short_name": "myActionGroup",
    "aggregation": "Average",
    "alert_description": "App Gateway backend pool unhealthy",
    "appgw_id": "/subscriptions/2da7649e-9fd1-4b68-a1b3-b9f4c429580e/resourceGroups/Infra/providers/Microsoft.Network/applicationGateways/devaks",
    "auto_mitigate": True,
    "enabled": True,
    "frequency": "PT1M",
    "function_app_webhook_url": "https://alertfapp.azurewebsites.net/api/alert",
    "location": "eastus",
    "operator": "GreaterThan",
    "resource_group_name": "alearts",
    "severity": 2,
    "threshold": 0,
    "use_common_alert_schema": True,
    "window_size": "PT5M",
}


def _build_appgw_backend_pool_alert(namespace: str, deployment_name: str, service_port: int) -> dict:
    alert_name = f"{deployment_name}-{namespace}-appgw-bp-unhealthy"
    payload = dict(_APPGW_BP_DEFAULTS)
    payload.update({
        "alert_name": alert_name,
        "namespace": namespace,
        "deployment_name": deployment_name,
        "service_port": service_port,
        "rg_tags": {
            "env": "infra",
            "project": namespace,
        },
    })
    return payload


def generate_appgw_backend_pool_alert_yaml(
    namespace: str,
    deployment_name: str,
    service_port: int,
    file_path: str = None,
) -> dict:
    """
    Generate an Application Gateway backend-pool unhealthy alert YAML for the
    given namespace + deployment, save it under <namespace>/alerts/, and upload
    it to blob storage.
    """
    try:
        alert = _build_appgw_backend_pool_alert(namespace, deployment_name, service_port)

        if not file_path:
            file_path = f"{namespace}/alerts/{alert['alert_name']}.yaml"

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as yaml_file:
            yaml.dump(alert, yaml_file, default_flow_style=False, sort_keys=True)

        result = upload_blob_to_azure(file_path, file_path)

        return {
            "message": f"Alert YAML file '{output_path}' created successfully.",
            "alert_name": alert["alert_name"],
            "alert": alert,
            "uploaded to storage account": str(result),
        }
    except Exception as e:
        return {"error": str(e)}
