from flask import Flask
from flask import render_template

app = Flask(__name__, static_folder="./static")


@app.route("/")
def home_page():
    return render_template("hello.html", name="test", data={})


if __name__ == "__main__":
    app.run()
