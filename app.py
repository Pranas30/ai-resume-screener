from flask import Flask, render_template, request, jsonify
import requests
import PyPDF2
import os

app = Flask(__name__)

# SECURITY STEP:
# We get the key from Render's settings, not hardcoded here.
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- THE LOGIC THAT WORKED FOR YOU (Using Requests) ---
def get_gemini_response(prompt):
    if not API_KEY:
        return "Server Error: API Key is missing. Please set GEMINI_API_KEY in Render settings."

    # We use the direct URL to avoid library version issues
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # If Flash fails (404), try Pro automatically
        if response.status_code == 404:
            fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
            response = requests.post(fallback_url, headers=headers, json=data)

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
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    job = request.form.get('job_desc')
    files = request.files.getlist('files')
    results = []

    for file in files:
        txt = extract_text(file)
        if not txt:
            results.append({"name": file.filename, "score": 0, "reason": "Empty/Image PDF"})
            continue
            
        prompt = f"""
        Role: Recruiter. Job: {job[:1000]}. Resume: {txt[:3000]}.
        Output strictly: "SCORE | REASON" (e.g. "85 | Good skills")
        """
        
        ai_reply = get_gemini_response(prompt)
        
        try:
            # Clean up response
            clean_reply = ai_reply.replace('*', '').replace('`', '').strip()
            if "|" in clean_reply:
                s, r = clean_reply.split('|', 1)
                results.append({"name": file.filename, "score": int(s.strip()), "reason": r.strip()})
            else:
                results.append({"name": file.filename, "score": 0, "reason": clean_reply[:100]})
        except:
             results.append({"name": file.filename, "score": 0, "reason": "Processing Error"})

    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results)

if __name__ == '__main__':
    # This configuration is required for Render/Heroku
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)