from scripts import init
from scripts import chat_gpt
from flask_socketio import SocketIO
from flask import Flask, render_template
from dotenv import load_dotenv, set_key

load_dotenv()


app = Flask(__name__)
socketio = SocketIO(app)

save_data_cache, system_prompts = init.load_and_embed()

@socketio.on("submit_question")
def handle_question(data):
    response, relevant_results = chat_gpt.ask_question(data["question"], save_data_cache, system_prompts, socketio)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app)
