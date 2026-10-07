from azure.storage.blob import BlobServiceClient
import os

def upload_blob_to_azure(blob_name, file_path):
    """
    Uploads a file to an Azure Blob Storage container.

    Args:
    - connection_string (str): The Azure Storage account connection string.
    - container_name (str): The name of the container to upload the blob to.
    - blob_name (str): The name of the blob in the container.
    - file_path (str): The local file path of the blob to upload.

    Returns:
    - str: Success message upon successful upload.
    """

    try:
        # Create BlobServiceClient from the connection string
        blob_service_client = BlobServiceClient.from_connection_string(
            os.getenv('CONNECTION_STRING'))

        # Get the container client
        container_client = blob_service_client.get_container_client(
            os.getenv('CONTAINER_NAME'))

        # Create a BlobClient to interact with the blob
        blob_client = container_client.get_blob_client(blob_name)

        # Upload the file
        with open(file_path, "rb") as data:
            # Set overwrite to True to replace an existing blob
            blob_client.upload_blob(data, overwrite=True)

        return f"Blob '{blob_name}' uploaded successfully to container '{os.getenv('CONTAINER_NAME')}'."

    except Exception as e:
        return f"An error occurred: {e}"

