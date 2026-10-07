
import requests
import base64
import json

organization = "pocadmin0421"
personal_access_token = "FzcYJSwY3OXd5AsodunNOYJ71DC2gXUfNsA0OVuSXgNdCZ0phqjaJQQJ99AKACAAAAASrjPtAAASAZDOTSbS"

def get_branches(organization, project, repository):

    url = f"https://dev.azure.com/{organization}/{project}/_apis/sourceProviders/TfsGit/branches"

    params = {
        "api-version": "7.2-preview.1",
    }
    
    if repository:
        params["repository"] = repository

    headers = {
        "Authorization": f"Basic {personal_access_token}",
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse and return branch names
        branches = response.json()
        return branches  # Branch list in response

    except requests.exceptions.RequestException as e:
        return f"Error fetching branches: {e}"


def get_repos(project):

    try:
        url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?includeLinks=False&includeAllUrls=False&includeHidden=False&api-version=7.2-preview.1"
        auth_token = base64.b64encode(
            f":{personal_access_token}".encode("ascii")).decode("ascii")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {auth_token}"
        }

        response = requests.get(url, headers=headers)

        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response = json.loads(response.text)
        
        branch = []
        for i in response['value']:
            for j in i:
                branch.append(get_branches(organization, project, j["name"]))
        return json.loads(branch)

    except requests.exceptions.RequestException as ex:
        print(f"An error occurred: {ex}")


def get_projects():

    try:
        url = f"https://dev.azure.com/{organization}/_apis/projects"

        # Create the authorization header
        auth_token = base64.b64encode(
            f":{personal_access_token}".encode("ascii")).decode("ascii")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {auth_token}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = json.loads(response.text)  # Print the JSON response
        resp = []

        for i in data["value"]:
            resp.append(get_repos(i["name"]))

        with open("repos.json", "w") as json_file:
            json.dump(resp, json_file, indent=4)

    except requests.exceptions.RequestException as ex:
        print(f"An error occurred: {ex}")

get_projects()