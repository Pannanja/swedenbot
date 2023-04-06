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
from scripts import config
from scripts import init

OPENAI_PROPERTIES = {
    "token_model" : "gpt-3.5-turbo",
    "embed_model" : "text-embedding-ada-002",
    "temperature" : 0.2,
    "streaming" : True,
    "max_tokens_in_system_prompt" : 2700
}

DATA = {
    "books_folder" : "books",
    "book_ext" : "txt",
    "embed_folder" : "data",
    "embed_ext" : "embed"
}

#CODE START------------------

#Loads API key

load_dotenv()
openai.api_key = os.environ.get("api-token")

if openai.api_key == None:
    api_token = input("No API key detected. Create a .env file in the same folder as this, and put in it api-token = 'insert token here'. You get your token from https://platform.openai.com/")
    exit()

#Finds and processes new books

new_book_files = misc.find_unproccessed_files(DATA["books_folder"], DATA["embed_folder"])

if len(new_book_files) != 0:
    new_book_file_names = ', '.join(new_book_files).replace('_', ' ').replace(f'.{DATA["book_ext"]}','').title()

    if len(new_book_files) == 1:
        user_input = input(f"New book detected: {new_book_file_names}. Embed? Y/N: ")
    else:
        user_input = input(f"New books detected: {new_book_file_names}. Embed? Y/N: ")

    if user_input.lower() == "y":
        for file_name in new_book_files:
            new_embedding = embed.new_embedding(file_name, OPENAI_PROPERTIES)
            misc.save_file(new_embedding, file_name.split(".")[0], DATA["embed_folder"], DATA["embed_ext"])


#Loads embed files to save_data_cache

embed_file_list = glob.glob(os.path.join(DATA["embed_folder"], f'*.{DATA["embed_ext"]}'))

if len(embed_file_list) == 0:
    input("No books detected. Download markup files from New Christian Bible Study and put them in the 'books' folder. Alternatively, message me for an email of the files.")
    exit()

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

system_prompts = {}
with open("prompts.txt", "r") as prompts:
    for prompt in prompts:
        stripped_prompt = prompt.strip()
        if stripped_prompt:
            name, text = stripped_prompt.split(' = ')
            system_prompts[name] = text

#Ask Questions!

while True: 
    if config.SOFTWARE_MODEL == "ncbs":
        user_question = sys.argv[1]
    else:
        user_question = input("Ask Question: ")
    embed_search_terms = chat_gpt.chat_gpt(system_prompts["query_rewrite"], user_question, OPENAI_PROPERTIES, None)[0]
        
    sorted_embeds = chat_gpt.find_relevant_embeds(embed_search_terms, OPENAI_PROPERTIES, save_data_cache)

    system_prompt_with_embeds, relevant_results = chat_gpt.append_embeds(sorted_embeds, system_prompts["swedenbot"], OPENAI_PROPERTIES)

    gtp_reply, gtp_message_history = chat_gpt.chat_gpt(system_prompt_with_embeds, user_question, OPENAI_PROPERTIES, None)
    print(relevant_results)