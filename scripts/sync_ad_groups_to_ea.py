import requests
from databricks.sdk import AccountClient
from databricks.sdk.core import DatabricksError
from databricks.sdk.service import iam
import argparse
import json

def get_access_token(spn_id, spn_key):
    post_data = {'client_id': spn_id,
                 'scope': 'https://graph.microsoft.com/.default',
                 'client_secret': spn_key,
                 'grant_type': 'client_credentials'}
    initial_header = {'Content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token", data=post_data, headers=initial_header)
    return response.json().get("access_token")

def find_current_groups_in_ea(sp_object_id):
    def extract_dict(resp_list):
        return [{
            "groupName": grp.get("principalDisplayName").lower(),
            "groupId": grp.get("principalId"),
            "assignmentId": grp.get("id")
            } for grp in resp_list]
            
    all_data = []
    header = {"Authorization": f"Bearer {token}"}
    req_url = f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo"

    while req_url:
        response = requests.get(req_url, headers=header)

        if response.status_code == 200:
            data = response.json()
            all_data.extend(extract_dict(data['value']))

            # Check if there are more pages
            req_url = data.get('@odata.nextLink')
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break

    return all_data 


def get_group_id(name):
    response = requests.get(
        f"{base_url}/groups?$filter=startswith(displayName,'{name}')&$count=true&$top=1", headers=header)
    if response.status_code == 200:
        res_json = response.json().get("value")
        if len(res_json) == 1:
            group = res_json[0]
            return ({"groupId": group.get("id"), "groupName": group.get("displayName")})
        else : 
            print(f"Group - {name} search failed : {response.json()}")
            return None


def add_group_to_ea(group):
    group_id = group.get("groupId")
    group_name = group.get("groupName")
    header = {"Authorization": f"Bearer {token}",
              'Content-type': 'application/json'}
    post_data = {
        "principalId": group_id,
        "resourceId": sp_object_id,
        "appRoleId": spn_app.get("roleId")
    }
    response = requests.post(
        f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo", headers=header, json=post_data)

    if (response.status_code == 201):
        print(f"\t Successfully added group -> {group_name} to Enterprise App")

def add_group_to_databricks_account(group):
    try :
        group = ac.groups.create(id="",display_name=group)
        print(f"\t Successfully added group into Databricks -> {group} ")
    except DatabricksError as e:
        if "already exists" in e.__str__() :
            print(f"\t Group already exists in Databricks -> {group}" )

def add_spns_to_databricks_account(group):
    group_id = group.get("groupId")
    group_name = group.get("groupName")
    response = requests.get(f"{base_url}/groups/{group_id}/members/microsoft.graph.servicePrincipal", headers=header)
    if(response.status_code == 200):
        res_json = response.json().get("value")
        if len(res_json) > 0 :
            for spn in res_json : 
                spn_app_id = spn.get("appId")
                try :
                    db_spn = ac.service_principals.create(application_id=spn_app_id)
                    spn["db_id"] = db_spn.id
                    add_spn_to_databricks_group(spn,group)
                except DatabricksError as e:
                    if "already exists in this account" in e.__str__() :
                        filter_query = f'applicationId eq "{spn.get("appId")}"'
                        resp = ac.service_principals.list(filter=filter_query)
                        spn["db_id"] = resp[0].id
                        print(f"\t Service Principal already exists in Databricks -> {spn_app_id} ")
                        add_spn_to_databricks_group(spn,group)
                        break
        else :
            print(f"\t No  Service Principals present in the group -> {group_name}")

def add_spn_to_databricks_group(spn, group):
    group_name = group.get("groupName")
    spn_app_id = spn.get("appId")
    filter_query = f'displayName eq "{group_name}"'
    resp = ac.groups.list(filter=filter_query)
    if(len(resp) == 1):
        db_group = resp[0]
        members_list = [d.display for d in db_group.members] if db_group.members is not None else []
        if(not spn_app_id in members_list) :
            value= {'members' : [{'value': spn.get("db_id")}]}
            operation = [iam.Patch(op=iam.PatchOp.ADD,value=value)]
            try: 
                ac.groups.patch(db_group.id,
                            schema=[iam.PatchSchema.URN_IETF_PARAMS_SCIM_API_MESSAGES_2_0_PATCH_OP],
                            operations=operation)
                print(f"\t Successfully added Service Principal -> {spn_app_id} to Group -> {db_group.display_name} in Databricks.")
            except DatabricksError as e:
                print(f"\t Patch API failed with error : {e.__str__()}")
        else :
            print(f"\t Service Principal {spn_app_id} is already present in Databricks group -> {db_group.display_name}" )

def remove_group_from_ea(group):
    assignment_id = group.get("assignmentId")
    group_name = group.get("groupName")
    response = requests.delete(
        f"{base_url}/servicePrincipals/{sp_object_id}/appRoleAssignedTo/{assignment_id}", headers=header)
    if (response.status_code == 204):
        print(f"\tSuccessfully removed group -> {group_name}")


def find_app(appName):
    response = requests.get(
        f"{base_url}/servicePrincipals?$filter=startswith(displayName,'{appName}')&$count=true&$top=1", headers=header)
    if response.status_code == 200:
        if len(response.json().get("value")) == 1:
            group = response.json().get("value")[0]
            return_obj = {"appId": group.get("appId"),
                     "roleId": group.get("appRoles")[0].get("id"),
                     "objectId": group.get("id")}
            print(f"Found EA : {return_obj}")
            return (return_obj)
    else :
        print(f"SPN app - {app_name} search failed : {response.json()}")

if __name__ == "__main__":

    base_url = "https://graph.microsoft.com/beta"

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("app_name", help="EA_app_name")
    arg_parser.add_argument("json_file_name", help="JSON file containing all groups")
    arg_parser.add_argument("tenant_id", help="Tenant Id")
    arg_parser.add_argument("spn_id", help="Deployment SPN ID")
    arg_parser.add_argument("spn_key", help="Deployment SPN Secret Key")
    args = vars(arg_parser.parse_args())

    groups_file_name = args["json_file_name"]
    app_name = args["app_name"]
    tenant_id = args["tenant_id"] # Azure Tenant id
    token = get_access_token(args["spn_id"], args['spn_key'])

    f = open(groups_file_name)
    all_groups = json.load(f)
    current_list = [x.lower() for x in all_groups]
    
    header = {"Authorization": f"Bearer {token}"}
    spn_app = find_app(app_name)
    sp_object_id = spn_app.get("objectId")

  
    ac = AccountClient(
                     host = "https://accounts.azuredatabricks.net/"
                    ,account_id = "df7062b8-3517-4cac-9415-861af2e7195f"
                    ,auth_type='azure-cli'
                    ,debug_truncate_bytes = 1000
                    )
    
    existing_groups = find_current_groups_in_ea(spn_app.get("objectId"))
    existing_groups_list = [d.get('groupName') for d in existing_groups]
    print(f"Total count of groups in Enterprise App : {len(existing_groups_list)}")

    # Add new groups
    add_groups = list(set(current_list) - set(existing_groups_list))

    print(f"Total Count of Groups to be added : {len(add_groups)}")
    print(f"Groups to be added : {add_groups}")

    for g in add_groups:
        print(f"Processing Group -> {g}.")
        grp = get_group_id(g)
        if(grp is not None):
            add_group_to_ea(grp)
            add_group_to_databricks_account(grp.get("groupName"))
            add_spns_to_databricks_account(grp)
        else:
            print(f"Skip processing {g} as its not a valid group name.")

    # Commenting out group removal logic.

    # # Remove stale groups
    # remove_groups = list(set(existing_groups_list) - set(current_list))
    # print(f"Groups to be removed : {remove_groups}")
    # for g in remove_groups:
    #     for grp in existing_groups:
    #         if (g == grp.get("groupName")):
    #             remove_group_from_ea(grp)
