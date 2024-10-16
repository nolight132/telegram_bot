import requests


API_URL = 'https://api.quotable.io'
authors = []
for i in range(1,requests.get(API_URL + "/authors?limit=150").json()["totalPages"] + 1):
    authors_response = requests.get(API_URL + f"/authors?page={i}&limit=150&sortBy=name")
    for author in authors_response.json()["results"]:
        authors.append(author["name"])
        
print(authors)
for author in authors:
    if 'napole'.capitalize() in author: print(True)