import concurrent.futures
import requests
import csv
import time
from datetime import datetime



isbnList = []
vintedSearchURL = 'https://www.vinted.de/api/v2/catalog/items?page=1&per_page=96&catalog_ids=2312&status_ids=3,2,1,6&search_text='
foundList = []
savedCookies = {}

def search(listSring):
    isbnprice = listSring.split(',')
    search(isbnprice[0], float(isbnprice[1]), isbnprice[2])

def search(isbn, price, rburl, getCookies = False):
    global savedCookies, foundList
    headers = { 'Accept-Language': 'de',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*', 'X-CSRF-Token': '75f6c9fa-dc8e-4e52-a000-e09dd4084b3e'}
 
    if getCookies or len(savedCookies) < 2:
        resp = requests.get('https://vinted.de')
        savedCookies = resp.cookies
    
    url = vintedSearchURL + isbn
    resp = requests.get(url, headers=headers, cookies=savedCookies)
    try:
        data = resp.json()
    except:
        print("Exception - json parse error")
        return
    
    print(data)
    try:
        for element in data["items"]:
            if float(element['price']) <= price:
                print(element['price'] + " URL: " + element['url'])
                dif = price - float(element['price'])
                timestamp = element['photo']['high_resolution']['timestamp']
                dt = datetime.fromtimestamp(timestamp)
                date_time = dt.strftime("%Y-%m-%d_%H%M%S")
                foundList.append(element['url'] + ',' + rburl + ','+ element['price'] + ',' + str(price) + ',' + isbn + ',' + str(dif) + ',' + date_time )
    except:
        print("Exception - Sleeping 30 sec")
        time.sleep(30)
        search(isbn, price, rburl, True)  
   
def buildList():
    with open("awin_feed_clean.csv", "r", encoding="utf8") as csvfile:   
        lines = csv.reader(csvfile, delimiter=',')
        for line in lines:
            isbnList.append(line[3] + ',' + line[2] + ',' + line[0])
    
    
def main():
    buildList()
    
    
    i = 0
    isLen = len(isbnList)
    for isbn in isbnList:
        isbnprice = isbn.split(',')
        search(isbnprice[0], float(isbnprice[1]), isbnprice[2])
        i = i+1
        print('tried: ' + str(i) + ' of ' + str(isLen))
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H%M%S")
    with open("vinted_"+date_time+".csv", "w") as file:
        print("Starting to write to disk")
        file.write('vinted_url,rebuy_url,vinted_price,rebuy_price,isbn,dif,dateuploaded\n')
        for line in foundList:
            file.write(line+'\n')

if __name__ == '__main__':
    main()