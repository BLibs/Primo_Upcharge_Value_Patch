import json
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import max_workers, desired_columns, headers


# Takes two parameters, establishment number as int and category name. Pulls all items from the categories
def get_category_data(establishment, category_name):
    # Endpoint
    url = "https://primohoagies.revelup.com/products/ProductCategory/"

    # Passing the supplied variables to request through query string along with a limit
    querystring = {"establishment": establishment, "name": category_name, "limit": 40}

    response = requests.request("GET", url, headers=headers, params=querystring)

    ''' Getting the name of the item and the product ID associated with it from the endpoint '''
    # Converting the data from response into JSON
    data = response.json()
    # Getting the 'subcategories' from the JSON, nested within the 'objects' key
    subcategories = data.get("objects", [{}])[0].get("subcategories", [])

    # Creating a list of name: 'item name' , id: 'item id' that we are going to return to the main function
    # For each category in subcategories, create an entry where name is 'name' and id is 'id'.
    name_id_list = [{"name": category["name"], "id": category["id"]} for category in subcategories]

    # Return the list
    return pd.DataFrame(name_id_list)


# Get the data on the products given the establishment and the product id
def get_product_data(est, cat_id):
    url = 'https://primohoagies.revelup.com/resources/Product/'
    # Passing the 'est' and 'cat_id' in to the parameters on the call
    params = {"establishment": est, "category": cat_id, "limit": 1000}
    response = requests.get(url, headers=headers, params=params)

    # Returning the response from the endpoint as JSON data
    return response.json()


# Getting data from multiple endpoints (establishments) in parallel to speed up the operation
def fetch_data_in_parallel(start_est, end_est):
    # Empty list that we will use to keep all data
    all_product_data = []

    # Setting a ThreadPoolExecutor with max_workers (defined in config) as 'executor'
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        ''' Using a thread pool to handle running these sequentially. Opting to hold these future objects in a dict
         so we can quickly reference the establishment number for print statement within this function. Otherwise,
         we would have to return this value from the process_establishment_data function. Could easily be held in a 
         list as well, but this is why I chose to design it like this. 
         
         future_pool is a dict object where the key is a call to the executors(ThreadPool name defined on creation)
         submit function. The submit function creates a future object, which we are linking to the 
         process_establishment_data function. This function takes one argument for the establishment number, passed
         in after the call to the function. We are creating a key value pair for each establishment within the range
         of start_est and end_est+1 (+1 added so loop includes the end_est number), where the key is the future object
         and the value is the establishment number.'''
        future_pool = {executor.submit(process_establishment_data, est): est for est in range(start_est, end_est+1)}

        ''' All futures run once they called the submit function. as_completed will let us know when the future is 
        finished running. This will also free up another worker for the next future to be created. So, for each future 
        that has completed in the future_pool...'''
        for future in as_completed(future_pool):
            # Get the value that is assigned to the key (est number)
            est = future_pool[future]
            try:
                # If the pool ran successfully, the returned data can be accessed from the future with .result()
                data = future.result()
                ''' We then take that data and extend it to the data list. Using extend because append would create a 
                list of lists. We want a singular list of items, which extend accommodates. [1,2,3] instead of 
                 [[1], [2,3]] for example. We want all data merged as it comes into pool from each future.'''
                all_product_data.extend(data)
                # Output the result, referencing which est has finished as it finishes
                print(f"\nData collection completed for establishment: {est}")
            except Exception as exc:
                # If there is an exception, we output the exception and the est
                print(f"\nEstablishment {est} generated an exception: {exc}")

    # Once finished, we return all the product data
    return all_product_data


# Takes establishment number as parameter. Calls get on catering options, filters out dirty data. Merges data into df
def process_establishment_data(est):
    print(f"\nStarting data processing for establishment: {est}")
    # Getting the initial data from all objects from the endpoint with the category name 'Catering'
    df_initial_catering = get_category_data(est, "Catering")
    ''' Using negate ~ on df to evaluate each entry and only populate the new data frame if the 'name' is not equal 
    to either option in the list provided to isin() function. In this case, if the 'name' is 'Catering' or 'Tray Sides',
    we don't want those items. If false, which ~ implies, we keep the item.
     
     This is done to exclude a few one off items that exist but won't require patching.'''
    df_initial_catering = df_initial_catering[~df_initial_catering['name'].isin(['Catering', 'Tray Sides'])]

    # Same thing done for the '• Catering' category items (online ordering menu)
    df_initial_dot_catering = get_category_data(est, "• Catering")
    df_initial_dot_catering = df_initial_dot_catering[~df_initial_dot_catering['name'].isin(['Catering', 'Tray Sides'])]

    # Once items that we don't want are filtered out, we combine the dataframes with concat, ignoring indexing
    df_combined = pd.concat([df_initial_catering, df_initial_dot_catering], ignore_index=True)

    # Now that we have the items that we want to target, we are going to get their full data
    filtered_data = []
    # For each item id in the combined dataframe...
    for cat_id in df_combined["id"]:
        # Get the data of the product
        product_data = get_product_data(est, cat_id)
        ''' Extend each item to the list created earlier for holding all the data. For each item, we are saying that
        for each column name in desired column list (all values we need to evaluate or patch the item through the 
        API endpoint), we are going to get the value of the key.'''
        filtered_data.extend(
            [{col: item.get(col, None) for col in desired_columns} for item in product_data.get("objects", [])]
        )

    # Once finished, return all the data. We now have everything we need to patch the items in patch_data.py
    return filtered_data


# Getting the maximum establishment ID. Will tell the script where to stop on data collection
def get_est_count():
    # Calling a GET to the enterprise establishment endpoint
    url = "https://primohoagies.revelup.com/enterprise/Establishment/"

    # 'fields' allows us to filter the data on the call, returning easier to parse data
    querystring = {"fields": "name,id"}
    response = requests.request("GET", url, headers=headers, params=querystring)

    # Converting response to JSON, using loads to convert to list to get the id of the last element returned
    data = json.loads(response.text)
    # Getting the 'id' from the last object in the list created above (data -> objects -> [-1 = last] -> 'id': x)
    last_id = data['objects'][-1]['id']

    return last_id
