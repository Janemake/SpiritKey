# Libraries required for the Bot (if using replit it will done automatically)
import os
import requests

# Based on KODADOT RMRK SUbQuery RMRK projects extraction
url = "https://api.subquery.network/sq/vikiival/magick"
        
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
                    events
                }
            }
        }
    }
  
}
"""
# Specify the variables
variables = {"CollectionValue": "Talisman Spirit Keys"}	


# 
def run_query(query, items): 
    request = requests.post(url, json={'query': query, 'variables': items})
    if request.status_code == 200: 
        #print("200")
        return request.json()
    else: 
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))



# Generate the list of the owner, seller and gift
def CheckKeys(addr, my_extract):
  # List of current owner
  SpiritKeyList = my_extract["data"]['collectionEntities']['nodes'][0]['nfts']['nodes'] # Drill down the dictionary
  owner = [d_owner['currentOwner'] for d_owner in SpiritKeyList if d_owner['currentOwner'] == addr]
  
# Initialize the lists
  itemListed =[]
  Gift =[]
  itemBought =[]

  # List of user of actions done on Spirit Keys
  for i in range(len(SpiritKeyList)):
    itemListed += [d_list['caller'] for d_list in SpiritKeyList[i]['events'] if ('caller' in d_list and d_list['interaction']=='LIST' and d_list['caller'] == addr) ]
    Gift += [d_list['caller'] for d_list in SpiritKeyList[i]['events'] if ('caller' in d_list and d_list['interaction']=='SEND' and d_list['caller'] == addr) ]
    itemBought += [d_list['caller'] for d_list in SpiritKeyList[i]['events'] if ('caller' in d_list and d_list['interaction']=='BUY' and d_list['caller'] == addr) ]
  return (len(owner), len(itemListed), len(Gift), len(itemBought))



result = run_query(query, variables) # Execute the query

input_address= input("Enter KSM address: ")

def checkSpiritKeys(user_address):
    keyOwned, KeySold, keyGave, keyBought = CheckKeys(user_address, result)
    print("\n\n  The address {}: \n  owns {} spirit Keys,  bought {}, sold {}  and sent {} \n\n ".format(user_address, keyOwned, keyBought,KeySold, keyGave))


checkSpiritKeys(input_address)