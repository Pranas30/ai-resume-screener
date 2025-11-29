from flask import Flask, request, jsonify, send_file, render_template_string
import requests
import PyPDF2
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder (Render uses ephemeral storage, which is fine for demos)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================
# 🔒 SECURITY: GET KEY FROM RENDER SETTINGS
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# 🎨 YOUR FRONTEND CODE (Embedded here for safety)
# ==========================================
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Analyzer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .form-group { margin-bottom: 25px; }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.3s;
        }
        textarea:focus { outline: none; border-color: #667eea; }
        input[type="file"] {
            width: 100%;
            padding: 15px;
            border: 2px dashed #667eea;
            border-radius: 10px;
            cursor: pointer;
            background: #f8f9ff;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        #results { margin-top: 40px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }
        tr:hover { background: #f8f9ff; }
        .rank {
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
        }
        .score {
            font-size: 1.3em;
            font-weight: bold;
        }
        .score-high { color: #10b981; }
        .score-medium { color: #f59e0b; }
        .score-low { color: #ef4444; }
        .resume-name {
            color: #667eea;
            cursor: pointer;
            text-decoration: underline;
            font-weight: 600;
        }
        .resume-name:hover { color: #764ba2; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 AI Resume Analyzer</h1>

        <form id="analyzeForm">
            <div class="form-group">
                <label>Job Description:</label>
                <textarea name="job_desc" rows="6" placeholder="Paste the job description here..." required></textarea>
            </div>

            <div class="form-group">
                <label>Upload Resumes (PDF):</label>
                <input type="file" name="files" accept=".pdf" multiple required>
            </div>

            <button type="submit">Analyze Resumes</button>
        </form>

        <div id="results"></div>
    </div>

    <script>
        document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = e.target.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'Analyzing...';

            const formData = new FormData(e.target);

            document.getElementById('results').innerHTML = '<div class="loading">🔍 Analyzing resumes... Please wait.</div>';

            try {
                const res = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                displayResults(data);
            } catch (err) {
                document.getElementById('results').innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Analyze Resumes';
            }
        });

        function displayResults(data) {
            if (data.length === 0) {
                document.getElementById('results').innerHTML = '<p>No results found.</p>';
                return;
            }

            let html = '<h2>📊 Results (Ranked by Match Score)</h2><table>';
            html += '<tr><th>Rank</th><th>Resume Name</th><th>Score</th><th>Analysis</th></tr>';

            data.forEach(item => {
                const scoreClass = item.score >= 70 ? 'score-high' : item.score >= 40 ? 'score-medium' : 'score-low';
                const medal = item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : '';

                html += `<tr>
                    <td class="rank">${medal} #${item.rank}</td>
                    <td><span class="resume-name" onclick="downloadResume('${item.filename}')">${item.name}</span></td>
                    <td class="score ${scoreClass}">${item.score}%</td>
                    <td>${item.reason}</td>
                </tr>`;
            });

            html += '</table>';
            document.getElementById('results').innerHTML = html;
        }

        function downloadResume(filename) {
            window.open(`/download/${filename}`, '_blank');
        }
    </script>
</body>
</html>
"""

def get_gemini_response(prompt):
    if not API_KEY:
        return "Server Error: API Key is missing. Please add 'GEMINI_API_KEY' to Render Environment Variables."

    # Using the model from your working code
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        # Fallback to 1.5-flash if 2.0 (experimental) fails on the server
        if response.status_code == 404:
             url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
             response = requests.post(url, headers=headers, json=data)

        if response.status_code != 200:
            return f"GOOGLE ERROR: {response.text}"

        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"System Error: {str(e)}"

def extract_text(file):
    try:
        pdf = PyPDF2.PdfReader(file)
        return "".join([p.extract_text() for p in pdf.pages])
    except: return ""

@app.route('/')
def home():
    # Renders the HTML string defined above
    return render_template_string(HTML_CODE)

@app.route('/analyze', methods=['POST'])
def analyze():
    job = request.form.get('job_desc')
    files = request.files.getlist('files')
    results = []

    for file in files:
        if file.filename == '': continue
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        txt = extract_text(open(filepath, 'rb'))

        if not txt:
            results.append({
                "name": filename,
                "score": 0,
                "reason": "Empty/Image PDF",
                "filename": filename
            })
            continue

        prompt = f"""
        Role: Recruiter. Job: {job[:1000]}. Resume: {txt[:3000]}.
        Output strictly: "SCORE | REASON" (e.g. "85 | Good skills")
        """

        ai_reply = get_gemini_response(prompt)

        try:
            if "|" in ai_reply:
                clean_reply = ai_reply.replace('*','').replace('`','')
                s, r = clean_reply.split('|', 1)
                results.append({
                    "name": filename,
                    "score": int(s.strip()),
                    "reason": r.strip(),
                    "filename": filename
                })
            else:
                 results.append({
                    "name": filename,
                    "score": 0,
                    "reason": ai_reply[:100],
                    "filename": filename
                })
        except:
            results.append({"name": filename, "score": 0, "reason": "Parsing Error", "filename": filename})

    results.sort(key=lambda x: x['score'], reverse=True)
    for i, result in enumerate(results):
        result['rank'] = i + 1

    return jsonify(results)

@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, mimetype='application/pdf')

if __name__ == '__main__':
    # Required for Render to find the correct port
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
