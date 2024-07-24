from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import subprocess
import os
import datetime
import uuid


app = Flask(__name__)
UPLOAD_FOLDER = 'output_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store job statuses
jobs = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_job', methods=['POST'])
def submit_job():
    script_name = request.form.get('script_name')
    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'pending', 'result': None}

    # Asynchronously run the script
    subprocess.Popen(['python3', script_name + '.py'],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Update job status
    jobs[job_id]['status'] = 'running'

    # Simulate job completion and storing result (for illustration)
    result_filename = os.path.join(
        UPLOAD_FOLDER, f'{script_name}_{job_id}.csv')
    jobs[job_id]['result'] = result_filename
    jobs[job_id]['status'] = 'completed'

    return jsonify({'job_id': job_id})


@app.route('/get_result', methods=['POST'])
def get_result():
    job_id = request.form.get('job_id')
    job = jobs.get(job_id)
    if job and job['status'] == 'completed':
        return jsonify({'status': 'completed', 'result': job['result']})
    return jsonify({'status': 'pending'})


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
