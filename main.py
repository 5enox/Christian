# app.py
from flask import Flask, send_file, render_template
import subprocess
import os
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run_rebuy')
def run_rebuy():
    subprocess.run(["python3", "rebuy.py"])
    return render_template('download.html', filename='awin_feed_clean.csv')


@app.route('/run_vinted')
def run_vinted():
    subprocess.run(["python3", "vinted.py"])
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d_%H%M%S")
    filename = f'vinted_{date_time}.csv'
    return render_template('download.html', filename=filename)


@app.route('/run_kleinanzeigen')
def run_kleinanzeigen():
    subprocess.run(["python3", "kleinanzeigen.py"])
    return render_template('download.html', filename='kleinanzeigen.csv')


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
