from flask import Flask, request, jsonify, render_template_string
import requests
import PyPDF2
import os

app = Flask(__name__)

# SECURITY: Get the key from Render's Environment Variables
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- HTML CODE INSIDE PYTHON (So you don't need a templates folder) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Resume Screener</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 40px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #333; }
        textarea { width: 100%; height: 120px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        .upload-box { border: 2px dashed #ccc; padding: 30px; text-align: center; margin-top: 20px; cursor: pointer; background: #fafafa; }
        button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 5px; font-weight: bold; margin-top: 20px; cursor: pointer; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; }
    </style>
</head>
<body>
<div class="container">
    <h1>🚀 AI Resume Screener</h1>
    <label><b>Job Description</b></label>
    <textarea id="job" placeholder="Paste Job Description..."></textarea>
    <div class="upload-box" onclick="document.getElementById('files').click()">
        📄 Click to Upload Resumes (PDF)
        <input type="file" id="files" multiple accept=".pdf" style="display:none" onchange="this.parentElement.innerText = this.files.length + ' files selected'">
    </div>
    <button onclick="analyze()" id="btn">Analyze Candidates</button>
    <div id="results" style="display:none; margin-top:20px;">
        <table><thead><tr><th>Candidate</th><th>Score</th><th>Reason</th></tr></thead><tbody></tbody></table>
    </div>
</div>
<script>
async function analyze() {
    const job = document.getElementById('job').value;
    const files = document.getElementById('files').files;
    if(!job || files.length === 0) return alert("Please enter a job description and upload files.");
    
    document.getElementById('btn').innerText = "Processing...";
    document.getElementById('btn').disabled = true;
    
    const fd = new FormData();
    fd.append('job', job);
    for(let f of files) fd.append('files', f);
    
    try {
        const res = await fetch('/analyze', {method:'POST', body:fd});
        const data = await res.json();
        const tbody = document.querySelector('tbody');
        tbody.innerHTML = '';
        data.forEach(d => {
            tbody.innerHTML += `<tr><td>${d.name}</td><td><b>${d.score}%</b></td><td>${d.reason}</td></tr>`;
        });
        document.getElementById('results').style.display = 'block';
    } catch(e) { alert("Error: " + e); }
    
    document.getElementById('btn').innerText = "Analyze Candidates";
    document.getElementById('btn').disabled = false;
}
</script>
</body>
</html>
"""

def get_gemini_response(prompt):
    if not API_KEY: return "Error: GEMINI_API_KEY not found in Render settings."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]})
        if response.status_code != 200:
             # Fallback to Pro if Flash fails
             url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
             response = requests.post(url, headers={'Content-Type': 'application/json'}, json={"contents": [{"parts": [{"text": prompt}]}]})
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e: return f"AI Error: {e}"

def extract_text(file):
    try:
        pdf = PyPDF2.PdfReader(file)
        return "".join([p.extract_text() for p in pdf.pages])
    except: return ""

@app.route('/')
def home():
    return render_template_string(HTML_CODE)

@app.route('/analyze', methods=['POST'])
def analyze():
    job = request.form.get('job')
    files = request.files.getlist('files')
    results = []
    for file in files:
        txt = extract_text(file)
        if not txt: continue
        prompt = f"Role: Recruiter. Job: {job[:1000]}. Resume: {txt[:3000]}. Output strictly: 'SCORE | REASON'"
        ai_reply = get_gemini_response(prompt)
        try:
            s, r = ai_reply.replace('*','').split('|', 1)
            results.append({"name": file.filename, "score": int(s.strip()), "reason": r.strip()})
        except:
            results.append({"name": file.filename, "score": 0, "reason": ai_reply[:100]})
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
