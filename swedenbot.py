import sys
from scripts import init
from scripts import chat_gpt
from scripts.config import config

software_model = config.get('model','software_model')

#Runs the init.py script, which performces bootup operations.
#save_data_cache is a dict which contains data from the embedded books
#system_prompts is the txt file in the op level folder full of system prompts
save_data_cache, system_prompts = init.load_and_embed()

if software_model == "ncbs":
    user_question = sys.argv[1]
    chat_gpt.ask_question(user_question, save_data_cache, system_prompts)
else:
    while True:
        user_question = input("Ask Question: ")
        chat_gpt.ask_question(user_question, save_data_cache, system_prompts)