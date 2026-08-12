import os
import base64
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import init_db, SessionLocal, Prompt

app = Flask(__name__)

# DATABASE INIT
init_db()

# GITHUB SETTINGS
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# HOME
@app.route("/")
def home():
    db = SessionLocal()
    prompts = db.query(Prompt).filter(Prompt.is_active == True).order_by(Prompt.created_at.desc()).all()
    db.close()
    return render_template("index.html", prompts=prompts)

# API
@app.route("/api/prompts")
def api_prompts():
    db = SessionLocal()
    prompts = db.query(Prompt).filter(Prompt.is_active == True).order_by(Prompt.created_at.desc()).all()
    db.close()
    
    result = []
    for p in prompts:
        result.append({
            "id": p.id,
            "title": p.title,
            "prompt": p.prompt,
            "category": p.category,
            "media_type": p.media_type,
            "media_url": p.media_url,
            "status": p.status
        })
    return jsonify(result)

# PROMPT DETAIL
@app.route("/prompt/<int:prompt_id>")
def prompt_detail(prompt_id):
    db = SessionLocal()
    prompt = db.query(Prompt).filter(
        Prompt.id == prompt_id,
        Prompt.is_active == True
    ).first()
    db.close()
    
    if not prompt:
        return "Prompt not found", 404
    
    return render_template("prompt_detail.html", prompt=prompt)

# ADMIN
@app.route("/admin")
def admin():
    db = SessionLocal()
    prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
    db.close()
    return render_template("admin.html", prompts=prompts)

# UPLOAD TO GITHUB
def upload_to_github(file):
    if not GITHUB_TOKEN:
        raise Exception("GITHUB_TOKEN environment variable missing")
    if not GITHUB_USERNAME:
        raise Exception("GITHUB_USERNAME environment variable missing")
    if not GITHUB_REPO:
        raise Exception("GITHUB_REPO environment variable missing")
    
    original_name = file.filename
    if not original_name:
        raise Exception("Invalid file name")
    
    filename = original_name.replace(" ", "_")
    github_path = f"uploads/prompts/{filename}"
    file_data = file.read()
    encoded_data = base64.b64encode(file_data).decode("utf-8")
    
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{github_path}"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    data = {
        "message": f"Upload prompt media: {filename}",
        "content": encoded_data,
        "branch": GITHUB_BRANCH
    }
    
    response = requests.put(api_url, headers=headers, json=data, timeout=60)
    
    if response.status_code not in [200, 201]:
        raise Exception(f"GitHub upload failed: {response.text}")
    
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{github_path}"
    return raw_url

# ADD PROMPT
@app.route("/admin/add-prompt", methods=["POST"])
def add_prompt():
    title = request.form.get("title", "").strip()
    prompt_text = request.form.get("prompt", "").strip()
    category = request.form.get("category", "funny").strip()
    status = request.form.get("status", "published").strip()
    media = request.files.get("media")
    
    if not title:
        db = SessionLocal()
        prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
        db.close()
        return render_template("admin.html", prompts=prompts, error="Title required hai.")
    
    if not prompt_text:
        db = SessionLocal()
        prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
        db.close()
        return render_template("admin.html", prompts=prompts, error="Prompt required hai.")
    
    if not media or not media.filename:
        db = SessionLocal()
        prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
        db.close()
        return render_template("admin.html", prompts=prompts, error="Image ya video upload karo.")
    
    try:
        media_url = upload_to_github(media)
        content_type = (media.content_type or "").lower()
        if content_type.startswith("video/"):
            media_type = "video"
        else:
            media_type = "image"
        
        db = SessionLocal()
        new_prompt = Prompt(
            title=title,
            prompt=prompt_text,
            category=category,
            media_type=media_type,
            media_url=media_url,
            status=status,
            is_active=True
        )
        db.add(new_prompt)
        db.commit()
        db.close()
        
        db = SessionLocal()
        prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
        db.close()
        
        return render_template("admin.html", prompts=prompts, message="✅ Prompt successfully add ho gaya!")
        
    except Exception as e:
        db = SessionLocal()
        prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
        db.close()
        return render_template("admin.html", prompts=prompts, error=str(e))

# DELETE PROMPT
@app.route("/admin/delete-prompt/<int:prompt_id>", methods=["POST"])
def delete_prompt(prompt_id):
    db = SessionLocal()
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    
    if prompt:
        prompt.is_active = False
        db.commit()
    
    db.close()
    return redirect(url_for("admin"))

# RUN
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
