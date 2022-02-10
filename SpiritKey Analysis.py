# Import the required libraries 
import os
import requests
import pandas as pd
import numpy as np

# Based on KODADOT RMRK SUbQuery RMRK projects extraction
url = "https://api.subquery.network/sq/vikiival/magick"

CL_END = "2021-11-24"  # Assumption for the last crowdloan distribution date of the keys! 
ALPHA_START = "2021-12-17" # Assumption of the start date for the Alpha

# The GraphQL query .       
query = """
query CheckAdress($CollectionValue: String!){
    collectionEntities (filter: {name: {equalTo: $CollectionValue}}) {
        nodes {
            name  
            nfts{
               nodes{
                    name
                    currentOwner
                    blockNumber
                    createdAt
                    events
                }
            }
        }
    }  
}
"""

# Specify the variables
variables = {"CollectionValue": "Talisman Spirit Keys"}	

# GET POST query
def run_query(query, items): 
    request = requests.post(url, json={'query': query, 'variables': items})
    if request.status_code == 200: 
        #print("200")
        return request.json()
    else: 
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))

# Generate the list of the owner, seller and gift
def CheckKeys(my_extract):    # List of collections with the same name.
    numb_collections = len(my_extract["data"]['collectionEntities']['nodes'])
    SpiritKeyList = []
    for i in range(numb_collections):
        SpiritKeyList += my_extract["data"]['collectionEntities']['nodes'][i]['nfts']['nodes'] # Drill down the dictionary
        # print(SpiritKeyList)

    # List of current owner
    owner = [[d_owner['currentOwner'],
              d_owner['name']
            ] 
             for d_owner in SpiritKeyList 
                if (d_owner['currentOwner'] != 'Gi9bsjnHLHmXHBaQW3Z8Hpjq7RN6ikGfbC12A49SMkzAqTh')
            ]
    # Initialize the lists
    acquisitionDate = []
    transactionsList =[]
    ListedForSale =[]
    remaingLists =[]
    
    # List of user of actions done on Spirit Keys
    for i in range(len(SpiritKeyList)):
        transactionsList += [
                                [
                                d_list['timestamp'][:10],
                                SpiritKeyList[i]['name'], 
                                d_list['blockNumber'], 
                                d_list['interaction'], 
                                d_list['caller'], 
                                d_list['meta']
                                ] 
                                    for d_list in SpiritKeyList[i]['events']
                                        if (d_list['caller'] != 'Gi9bsjnHLHmXHBaQW3Z8Hpjq7RN6ikGfbC12A49SMkzAqTh')
                            ]

        acquisitionDate  += [
                                [
                                    d_list['timestamp'][:10], 
                                    SpiritKeyList[i]['name'], 
                                    SpiritKeyList[i]['currentOwner'], 
                                    d_list['caller'],
                                    d_list['blockNumber'], 
                                    d_list['interaction'], 
                                ] 
                                    for d_list in SpiritKeyList[i]['events']
                                        if (d_list['meta'] == SpiritKeyList[i]['currentOwner'])
                            ]
        # Creation of the listing events lists based on the last event of the NFTs
        if (SpiritKeyList[i]['events'][-1]['interaction']=='LIST'):
            if  int(SpiritKeyList[i]['events'][-1]['meta'])>0:    
                ListedForSale += [[SpiritKeyList[i]['events'][-1]['timestamp'][:10], 
                                    SpiritKeyList[i]['name'], 
                                    SpiritKeyList[i]['events'][-1]['interaction'], 
                                    SpiritKeyList[i]['events'][-1]['blockNumber'], 
                                    SpiritKeyList[i]['events'][-1]['caller'], 
                                     int(SpiritKeyList[i]['events'][-1]['meta'])/(1000000000000*0.98) # include the commissions fees of 2% of RMRK
                                    ]
                                 ]

        if (SpiritKeyList[i]['events'][-1]['interaction'] in ['MINTNFT','MINT']):  
            remaingLists += [[SpiritKeyList[i]['name'],
                                SpiritKeyList[i]['events'][-1]['timestamp'][:10],
                                ]
                            ]

    # Dataframe of SK transactions activities
    df_transactions = pd.DataFrame(transactionsList, columns =["timestamp", "SK", "block", "Action", "Sender address", 'meta']).sort_values(by=['timestamp'])
    df_transactions.loc[ (df_transactions["Action"] == "SEND")  ,"Transaction type"] = "Gift"
    df_transactions.loc[ (df_transactions["Action"]  == "BUY")  ,"Transaction type"] = "Sale"
    df_transactions.loc[ (df_transactions["Action"]  == "LIST") & (df_transactions['meta']!= "0") ,"Transaction type"] = "Listing"
    df_transactions.loc[ (df_transactions["Action"]  == "LIST") & (df_transactions['meta']== "0")    ,"Transaction type"] = "Delisting"
    
    # Dataframe for the transfers events only 
    df_transfer =  df_transactions[df_transactions.Action.isin(["BUY","SEND"])].rename(columns = {'meta': "Receiver Address"})
    df_transfer.reset_index(inplace = True)
    df_transfer.drop(["index"], axis=1, inplace = True)

    # Dataframe for the listing events only 
    df_listing =  df_transactions[df_transactions.Action == "LIST"].rename(columns = {'meta': "Listing price", 'Sender address':'Seller address'})
    df_listing[ "Listing price"] = np.longdouble(df_listing[ "Listing price"])/(1000000000000*0.98) # include the commissions fees of 2% of RMRK
    df_listing.reset_index(inplace = True)
    df_listing.drop(["index"], axis=1, inplace = True)

    # Dataframe of SK listed for sales
    df_sales = pd.DataFrame(ListedForSale, columns =[ "timestamp", "SK", "Action", "block", "Seller address", 'price']).sort_values(by=['timestamp'])
    df_sales.reset_index(inplace = True)

    # Dataframe of SK acquisition period
    df_acquisition = pd.DataFrame(acquisitionDate, columns =["timestamp",  "SK", "Current Owner", "Previous Owner", "block", "Action"]).drop_duplicates(subset=['SK'], keep='first').sort_values(by=['timestamp'])
    df_acquisition.loc[ (df_acquisition["timestamp"] <= CL_END), "Acquisition period"] = "During Polkadot CL campaign"
    df_acquisition.loc[ (df_acquisition["timestamp"] > CL_END) & (df_acquisition["timestamp"] <= ALPHA_START), "Acquisition period"] = "Between CL campaign & Alpha launch"
    df_acquisition.loc[ (df_acquisition["timestamp"] > ALPHA_START), "Acquisition period"] = "After Alpha Launch"
    df_acquisition.loc[ (df_acquisition["Previous Owner"] == "Gi9bsjnHLHmXHBaQW3Z8Hpjq7RN6ikGfbC12A49SMkzAqTh"), "Previous Owner"] = "Talisman Minter"
    df_acquisition.loc[ (df_acquisition["Action"] == "SEND"), "Acquisition type"] = "Gift"
    df_acquisition.loc[ (df_acquisition["Action"]  == "BUY"), "Acquisition type"] = "Sale"
    df_acquisition.reset_index(inplace = True)
    
    # Unique address owner and grouping per number of keys owned
    df_owner = pd.DataFrame(owner, columns =["Address", "SK"])
    df_uniqueOwner = df_owner.groupby(["Address"]).count()
    df_uniqueOwner.loc[ (df_uniqueOwner["SK"] <= 2), "Group"] = "1 - 2 SKs"
    df_uniqueOwner.loc[ (df_uniqueOwner["SK"] > 2) & (df_uniqueOwner["SK"] <= 4), "Group"] = "3 - 4 SKs"
    df_uniqueOwner.loc[ (df_uniqueOwner["SK"] > 4), "Group"] = "5+ SKs"
    
    # Grouping of SK owners per number of SK owned
    df_group = df_uniqueOwner.groupby(["Group"]).count()
    df_class = df_uniqueOwner.groupby(["SK"]).count()

    # Generation of the excel file in the python file folder
    with pd.ExcelWriter("SK transactions details.xlsx") as writer:  # doctest: +SKIP
        df_acquisition[["timestamp",  "SK", "Current Owner",
                        "Previous Owner", "block", "Action", 
                        "Acquisition period", "Acquisition type"]].to_excel(writer, sheet_name="SK Acquisitions")
        df_sales[["timestamp", "SK", "Action", "block", 
                  "Seller address", 'price']].to_excel(writer, sheet_name="SK on sale")
        df_transfer[["timestamp", "SK", "block", "Action", "Sender address", "Receiver Address"]].to_excel(writer, sheet_name="SK transfers")
        df_listing[["timestamp", "SK", "block", "Action", "Seller address", 'Listing price']].to_excel(writer, sheet_name="SK listing activities")
        pd.DataFrame(remaingLists, columns =["SK", "Creation date"]).to_excel(writer, sheet_name="SK not distributed")
        df_uniqueOwner.to_excel(writer, sheet_name="Nb per address")
        df_group.to_excel(writer, sheet_name="Group of owner")
        df_class.to_excel(writer, sheet_name="Owner per class")


# Execute the POST query to fetch the data
result = run_query(query, variables) # Execute the query

# Execution of the code
CheckKeys(result)
