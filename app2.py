from flask import Flask, render_template, request, send_file
import os
from your_existing_script import generate_latex  # We will put your main logic here

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form.get("topic")
        num_list = int(request.form.get("num_list"))
        # generate the LaTeX file
        tex_file_path = generate_latex(topic, num_list)
        return send_file(tex_file_path, as_attachment=True)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=8000, debug=True)
