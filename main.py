from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import os
import uuid
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'output_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Store job status
current_job = {'status': 'idle', 'progress': 0, 'result': None}


@app.route('/')
def index():
    return render_template('index.html', job_status=current_job['status'], progress=current_job['progress'])


@app.route('/submit_job', methods=['POST'])
def submit_job():
    global current_job

    if current_job['status'] == 'running':
        return jsonify({'status': 'error', 'message': 'A job is already running. Please wait until it finishes.'})

    script_name = request.form.get('script_name')
    current_job = {'status': 'running', 'progress': 0, 'result': None}

    def run_script():
        global current_job
        try:
            process = subprocess.Popen(
                ['python3', script_name + '.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for line in process.stdout:
                if line.startswith(b'Progress:'):
                    current_job['progress'] = int(
                        line.decode().strip().split(':')[1])
                time.sleep(1)  # Simulate progress update delay
            process.wait()
            current_job['status'] = 'completed'
            current_job['result'] = os.path.join(
                UPLOAD_FOLDER, f'{script_name}.csv')
        except Exception as e:
            current_job['status'] = 'error'
            current_job['result'] = str(e)

    import threading
    thread = threading.Thread(target=run_script)
    thread.start()

    return jsonify({'status': 'ok'})


@app.route('/get_result', methods=['POST'])
def get_result():
    return jsonify({'status': current_job['status'], 'result': current_job['result'], 'progress': current_job['progress']})


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
