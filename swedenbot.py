import sys
from scripts import init
from scripts.config import config
from scripts import chat_gpt

software_model = config.get('model','software_model')
if software_model != "flask":
    save_data_cache, system_prompts = init.load_and_embed()
    while True:
        if software_model == "ncbs":
            user_question = sys.argv[1]
        else:
            user_question = input("Ask Question: ")
        chat_gpt.ask_question(user_question, save_data_cache, system_prompts)