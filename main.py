from flask import Flask, render_template, jsonify, request, send_from_directory
import requests
import gzip
import shutil
import csv
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'output_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Job status
progress = 0


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_rebuy', methods=['POST'])
def start_rebuy():
    global progress
    progress = 0
    # Run the rebuy task
    rebuy_task()
    return jsonify({'status': 'started'})


@app.route('/progress', methods=['GET'])
def get_progress():
    global progress
    return jsonify({'progress': progress})


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/start_vinted', methods=['POST'])
def start_vinted():
    global vinted_progress
    vinted_progress = 0
    # Run the vinted task
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(vinted_task)
    return jsonify({'status': 'started'})


@app.route('/vinted_progress', methods=['GET'])
def get_vinted_progress():
    global vinted_progress
    return jsonify({'progress': vinted_progress})


def rebuy_task():
    global progress
    minValue = 5.0
    feedURL = 'https://productdata.awin.com/datafeed/download/apikey/f409ea591dbab5db570543a201b9f2f2/language/de/cid/230,609,538/fid/77537,77663/rid/0/hasEnhancedFeeds/0/columns/aw_deep_link,product_name,search_price,ean/format/csv/delimiter/%2C/compression/gzip/adultcontent/1/'

    # Download the file
    resp = requests.get(feedURL)
    if resp.status_code == 200:
        with open("awin_feed.gz", "wb") as file:
            file.write(resp.content)
        progress = 25  # Update progress

        # Unzip the file
        with gzip.open('awin_feed.gz', 'rb') as f_in:
            with open('awin_feed.csv', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        progress = 50  # Update progress

        # Process the CSV file
        cleanList = []
        with open("awin_feed.csv", "r", encoding="utf8") as csvfile:
            lines = csv.reader(csvfile, delimiter=',')
            for line in lines:
                try:
                    price = float(line[2])
                except ValueError:
                    continue
                if price >= minValue:
                    cleanList.append(line)
        progress = 75  # Update progress

        # Create clean CSV
        with open(os.path.join(UPLOAD_FOLDER, 'awin_feed_clean.csv'), 'w', newline='', encoding="utf8") as newfile:
            writer = csv.writer(newfile)
            writer.writerows(cleanList)
        progress = 100  # Update progress

    else:
        progress = 0  # Update progress if failed


def search(isbn, price, rburl, get_cookies=False):
    global vinted_saved_cookies, vinted_found_list
    headers = {
        'Accept-Language': 'de',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'X-CSRF-Token': '75f6c9fa-dc8e-4e52-a000-e09dd4084b3e'
    }

    if get_cookies or len(vinted_saved_cookies) < 2:
        resp = requests.get('https://vinted.de')
        vinted_saved_cookies = resp.cookies

    url = vintedSearchURL + isbn
    resp = requests.get(url, headers=headers, cookies=vinted_saved_cookies)
    try:
        data = resp.json()
    except:
        print("Exception - json parse error")
        return

    try:
        for element in data["items"]:
            if float(element['price']) <= price:
                print(f"{element['price']} URL: {element['url']}")
                dif = price - float(element['price'])
                timestamp = element['photo']['high_resolution']['timestamp']
                dt = datetime.fromtimestamp(timestamp)
                date_time = dt.strftime("%Y-%m-%d_%H%M%S")
                vinted_found_list.append(f"{element['url']},{rburl},{element['price']},{
                                         price},{isbn},{dif},{date_time}")
    except:
        print("Exception - Sleeping 30 sec")
        time.sleep(30)
        search(isbn, price, rburl, True)


def build_list():
    global isbnList
    with open("awin_feed_clean.csv", "r", encoding="utf8") as csvfile:
        lines = csv.reader(csvfile, delimiter=',')
        for line in lines:
            isbnList.append(f"{line[3]},{line[2]},{line[0]}")


def vinted_task():
    global vinted_progress, vinted_found_list
    build_list()

    i = 0
    is_len = len(isbnList)
    for isbn in isbnList:
        isbn_price = isbn.split(',')
        search(isbn_price[0], float(isbn_price[1]), isbn_price[2])
        i += 1
        vinted_progress = int((i / is_len) * 100)  # Update progress
        print(f'Tried: {i} of {is_len}')

    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H%M%S")
    with open(os.path.join(UPLOAD_FOLDER, f"vinted_{date_time}.csv"), "w") as file:
        print("Starting to write to disk")
        file.write(
            'vinted_url,rebuy_url,vinted_price,rebuy_price,isbn,dif,dateuploaded\n')
        for line in vinted_found_list:
            file.write(line + '\n')
    vinted_progress = 100  # Complete progress


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
