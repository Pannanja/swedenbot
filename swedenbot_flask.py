from scripts import init
from scripts import chat_gpt
from flask_socketio import SocketIO
from flask import Flask, render_template
from dotenv import load_dotenv, set_key

load_dotenv()
save_data_cache = init.init_swedenbot()
app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on("submit_question")
def handle_question(data):
    question = data["question"]
    temperature = float(data["temperature"])
    chat_gpt.ask_swedenbot(question, save_data_cache, temperature, socketio)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app)
