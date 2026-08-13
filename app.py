# ==========================================
# app.py - Complete with Optional Photo Upload
# ==========================================

import os
import base64
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from functools import wraps

# Database import
from database import init_db, SessionLocal, Prompt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")

# ==========================================
# DATABASE INIT
# ==========================================

init_db()

# ==========================================
# GITHUB SETTINGS
# ==========================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# ==========================================
# ADMIN CREDENTIALS
# ==========================================

ADMIN_PHONE = "9355491854"
ADMIN_PASSWORD = "Aja@y123"

# ==========================================
# LOGIN DECORATOR
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        
        if phone == ADMIN_PHONE and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template("admin_login.html", error="❌ गलत ID या पासवर्ड!")
    
    return render_template("admin_login.html")

# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.route("/admin-logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# ==========================================
# HOME - USER SIDE
# ==========================================

@app.route("/")
def home():
    try:
        db = SessionLocal()
        prompts = db.query(Prompt).filter(Prompt.is_active == True).order_by(Prompt.created_at.desc()).all()
        db.close()
        return render_template("index.html", prompts=prompts)
    except Exception as e:
        return f"Database error: {e}", 500

# ==========================================
# API - GET PROMPTS
# ==========================================

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
            "category": p.category if hasattr(p, 'category') else "funny",
            "media_type": p.media_type,
            "media_url": p.media_url,
            "status": p.status if hasattr(p, 'status') else "published"
        })
    return jsonify(result)

# ==========================================
# PROMPT DETAIL
# ==========================================

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

# ==========================================
# ADMIN PANEL
# ==========================================

@app.route("/admin")
@login_required
def admin():
    db = SessionLocal()
    prompts = db.query(Prompt).order_by(Prompt.created_at.desc()).all()
    db.close()
    return render_template("admin.html", prompts=prompts)

# ==========================================
# UPLOAD FILE TO GITHUB
# ==========================================

def upload_to_github(file):
    if not GITHUB_TOKEN or not GITHUB_USERNAME or not GITHUB_REPO:
        return None
    
    try:
        original_name = file.filename
        if not original_name:
            return None
        
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
            return None
        
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{github_path}"
        return raw_url
        
    except Exception as e:
        print(f"GitHub upload error: {e}")
        return None

# ==========================================
# ADD PROMPT - With Optional Photo
# ==========================================

@app.route("/admin/add-prompt", methods=["POST"])
@login_required
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
    
    try:
        media_url = None
        media_type = "image"
        
        # Agar photo upload ki hai toh GitHub pe upload karein
        if media and media.filename:
            uploaded_url = upload_to_github(media)
            if uploaded_url:
                media_url = uploaded_url
                content_type = (media.content_type or "").lower()
                if content_type.startswith("video/"):
                    media_type = "video"
            else:
                # Agar upload fail ho toh placeholder
                media_url = f"https://picsum.photos/seed/{title.replace(' ', '')}/400/225"
        else:
            # Agar photo nahi upload ki toh placeholder
            media_url = f"https://picsum.photos/seed/{title.replace(' ', '')}/400/225"
        
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

# ==========================================
# DELETE PROMPT
# ==========================================

@app.route("/admin/delete-prompt/<int:prompt_id>", methods=["POST"])
@login_required
def delete_prompt(prompt_id):
    db = SessionLocal()
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    
    if prompt:
        prompt.is_active = False
        db.commit()
    
    db.close()
    return redirect(url_for("admin"))

# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
