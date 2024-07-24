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


if __name__ == '__main__':
    app.run(debug=True)
