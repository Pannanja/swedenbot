from dotenv import load_dotenv
import glob
import gzip
import openai
import os
import pickle
import sys
from tqdm import tqdm
from scripts import embed
from scripts import chat_gpt
from scripts import misc
from flask import Flask
from scripts.config import config



app = Flask(__name__)
@app.before_first_request
def load_and_embed():
    #Loads Config

    book_ext = config.get('data','book_ext')
    embed_ext = config.get('data','embed_ext')
    embed_folder = config.get('data','embed_folder')

    #Loads API key

    load_dotenv()
    openai.api_key = os.environ.get("api-token")

    if openai.api_key == None:
        api_token = input("No API key detected. Create a .env file in the same folder as this, and put in it api-token = 'insert token here'. You get your token from https://platform.openai.com/")
        exit()

    #Finds and processes new books

    new_book_files = misc.find_unproccessed_files()

    if len(new_book_files) != 0:

        new_book_file_names = ', '.join(new_book_files).replace('_', ' ').replace(f'.{book_ext}','').title()

        if len(new_book_files) == 1:
            user_input = input(f"New book detected: {new_book_file_names}. Embed? Y/N: ")
        else:
            user_input = input(f"New books detected: {new_book_file_names}. Embed? Y/N: ")

        if user_input.lower() == "y":
            for file_name in new_book_files:
                new_embedding = embed.new_embedding(file_name)
                misc.save_file(new_embedding, file_name.split(".")[0])


    #Loads embed files to save_data_cache

    embed_file_list = glob.glob(os.path.join(embed_folder, f'*.{embed_ext}'))

    if len(embed_file_list) == 0:
        input("No books detected. Download markup files from New Christian Bible Study and put them in the 'books' folder. Alternatively, message me for an email of the files.")
        exit()
    global save_data_cache
    save_data_cache = {
        "chunks" : [],
        "embeds" : [],
        "ref" : [],
    }

    for i in tqdm(range(len(embed_file_list)), desc="Loading Books"):
            with gzip.open(embed_file_list[i], 'rb') as file:
                temp_save_data = pickle.load(file)
                for key in temp_save_data:
                    save_data_cache[key].extend(temp_save_data[key])

    #Import system prompts from prompts.txt
    global system_prompts
    system_prompts = {}
    with open("prompts.txt", "r") as prompts:
        for prompt in prompts:
            stripped_prompt = prompt.strip()
            if stripped_prompt:
                name, text = stripped_prompt.split(' = ')
                system_prompts[name] = text

#Ask Questions!
@app.route('/')
def ask_question(user_question):
    embed_search_terms = chat_gpt.chat_gpt(system_prompts["query_rewrite"], user_question, None)[0]
            
    sorted_embeds = misc.find_relevant_embeds(embed_search_terms, save_data_cache)

    system_prompt_with_embeds, relevant_results = misc.append_embeds(sorted_embeds, system_prompts["swedenbot"])

    gtp_reply, gtp_message_history = chat_gpt.chat_gpt(system_prompt_with_embeds, user_question, None)
    print(relevant_results)
    return(gtp_reply)

#CODE START--------------------------------------

software_model = config.get('model','software_model')
if software_model != "flask":
    load_and_embed()
    while True:
        if software_model == "ncbs":
            user_question = sys.argv[1]
        else:
            user_question = input("Ask Question: ")
        ask_question(user_question)