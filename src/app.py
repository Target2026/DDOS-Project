from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start_ids", methods=["POST"])
def start_ids():
    os.system("python src/ids.py &")  
    return "✅ IDS Started Successfully!"

@app.route("/generate_fake_attack", methods=["POST"])
def generate_fake_attack():
    os.system("python src/attack_generator.py")
    return "✅ Fake Attack Traffic Generated!"

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    file = request.files["file"]
    file.save(os.path.join("data", file.filename))
    return f"✅ File {file.filename} uploaded successfully!"

if __name__ == "__main__":
    app.run(debug=True)
