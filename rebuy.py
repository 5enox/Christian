import requests
import gzip
import shutil
import csv

minValue = 5.0

feedURL = 'https://productdata.awin.com/datafeed/download/apikey/f409ea591dbab5db570543a201b9f2f2/language/de/cid/230,609,538/fid/77537,77663/rid/0/hasEnhancedFeeds/0/columns/aw_deep_link,product_name,search_price,ean/format/csv/delimiter/%2C/compression/gzip/adultcontent/1/'
print("Getting URL")
resp = requests.get(feedURL)
print("Done getting URL")

if resp.status_code == 200:
    with open("awin_feed.gz", "wb") as file:
        print("Starting to write to disk")
        file.write(resp.content)
        print("File downloaded successfully!")
else:
    print("Failed to download the file.")
    exit

print("Starting unzip")
with gzip.open('awin_feed.gz', 'rb') as f_in:
  with open('awin_feed.csv', 'wb') as f_out:
    print("Creating textfile")
    shutil.copyfileobj(f_in, f_out)
print("Done unzipping")

cleanList =[] 
print("Reading lines")
with open("awin_feed.csv", "r", encoding="utf8") as csvfile:
    lines = csv.reader(csvfile, delimiter=',')
    for line in lines:
        try:
            price = float(line[2])
        except ValueError:
                print("Not a number - Next")
                continue
        if(price >= minValue):
            cleanList.append(line)
            

print("Creating clean csv")
with open('awin_feed_clean.csv', 'w', newline='', encoding="utf8") as newfile:
    writer = csv.writer(newfile)
    writer.writerows(cleanList)
print("Clean CSV done")