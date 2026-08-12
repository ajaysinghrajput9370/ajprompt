from flask import Flask, render_template

from database import init_db


app = Flask(__name__)


# Database tables create
init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/prompt/<int:prompt_id>")
def prompt_detail(prompt_id):
    return render_template(
        "prompt.html",
        prompt_id=prompt_id
    )


@app.route("/admin")
def admin():
    return render_template("admin.html")


if __name__ == "__main__":
    app.run(debug=True)
