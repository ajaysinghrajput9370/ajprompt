import os
import base64
import requests

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from database import init_db, SessionLocal, Prompt


app = Flask(__name__)


# ==========================================
# DATABASE
# ==========================================

init_db()


# ==========================================
# GITHUB SETTINGS
# ==========================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

GITHUB_REPO = os.getenv("GITHUB_REPO")

GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main"
)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# ADMIN
# ==========================================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# ==========================================
# UPLOAD FILE TO GITHUB
# ==========================================

def upload_to_github(file):

    if not GITHUB_TOKEN:
        raise Exception("GITHUB_TOKEN missing")

    if not GITHUB_USERNAME:
        raise Exception("GITHUB_USERNAME missing")

    if not GITHUB_REPO:
        raise Exception("GITHUB_REPO missing")


    # File name
    original_name = file.filename

    if not original_name:
        raise Exception("Invalid file name")


    # Secure simple filename
    filename = original_name.replace(
        " ",
        "_"
    )


    # Folder in GitHub
    github_path = f"uploads/prompts/{filename}"


    # Read file
    file_data = file.read()


    # Convert to Base64
    encoded_data = base64.b64encode(
        file_data
    ).decode("utf-8")


    # GitHub API
    api_url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_USERNAME}/"
        f"{GITHUB_REPO}/contents/"
        f"{github_path}"
    )


    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


    data = {
        "message": f"Upload prompt media: {filename}",
        "content": encoded_data,
        "branch": GITHUB_BRANCH
    }


    response = requests.put(
        api_url,
        headers=headers,
        json=data,
        timeout=60
    )


    if response.status_code not in [200, 201]:

        raise Exception(
            f"GitHub upload failed: "
            f"{response.text}"
        )


    # GitHub Raw URL
    raw_url = (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_USERNAME}/"
        f"{GITHUB_REPO}/"
        f"{GITHUB_BRANCH}/"
        f"{github_path}"
    )


    return raw_url


# ==========================================
# ADD PROMPT
# ==========================================

@app.route(
    "/admin/add-prompt",
    methods=["POST"]
)
def add_prompt():

    title = request.form.get(
        "title",
        ""
    ).strip()


    prompt_text = request.form.get(
        "prompt",
        ""
    ).strip()


    media = request.files.get(
        "media"
    )


    # Basic validation
    if not title:

        return render_template(
            "admin.html",
            error="Title required hai."
        )


    if not prompt_text:

        return render_template(
            "admin.html",
            error="Prompt required hai."
        )


    if not media or not media.filename:

        return render_template(
            "admin.html",
            error="Image ya video upload karo."
        )


    try:

        # Upload media to GitHub
        media_url = upload_to_github(
            media
        )


        # Detect media type
        content_type = (
            media.content_type or ""
        ).lower()


        if content_type.startswith(
            "video/"
        ):

            media_type = "video"

        else:

            media_type = "image"


        # Save database
        db = SessionLocal()


        new_prompt = Prompt(

            title=title,

            prompt=prompt_text,

            media_type=media_type,

            media_url=media_url,

            is_active=True

        )


        db.add(
            new_prompt
        )

        db.commit()


        db.close()


        return render_template(
            "admin.html",
            message="✅ Prompt successfully add ho gaya!"
        )


    except Exception as e:

        return render_template(
            "admin.html",
            error=str(e)
        )


# ==========================================
# PROMPT DETAIL
# ==========================================

@app.route(
    "/prompt/<int:prompt_id>"
)
def prompt_detail(prompt_id):

    db = SessionLocal()

    prompt = db.query(
        Prompt
    ).filter(
        Prompt.id == prompt_id,
        Prompt.is_active == True
    ).first()

    db.close()


    if not prompt:

        return "Prompt not found", 404


    return render_template(
        "prompt.html",
        prompt=prompt
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
