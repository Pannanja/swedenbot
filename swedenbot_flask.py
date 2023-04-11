from scripts import init
from scripts import chat_gpt
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

save_data_cache, system_prompts = init.load_and_embed()

@app.route('/', methods=['GET', 'POST'])
def question_form():
    if request.method == 'POST':
        user_question = request.form['user_question']
        response = chat_gpt.ask_question(user_question, save_data_cache, system_prompts)
        return str(response)
    return render_template('question_form.html')
