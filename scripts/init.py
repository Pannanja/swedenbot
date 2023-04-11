#Standard Libraries
import os
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv, set_key

#Third Party Libraries
import glob
import openai
from tqdm import tqdm

#Local Imports
from scripts import chat_gpt
from scripts import embed
from scripts import misc
from scripts import multi_threading
from scripts import user_input
from scripts.config import config

def load_and_embed():

    #Loads Config

    book_ext = config.get('data','book_ext')
    embed_ext = config.get('data','embed_ext')
    embed_folder = config.get('data','embed_folder')

    #Loads API key

    load_dotenv()
    openai.api_key = os.environ.get("api-key")

    #Adds API key

    if openai.api_key == None:
        api_key = user_input.user_input("Enter OpenAI API key",str)
        openai.api_key = api_key
        set_key(".env","api-key",api_key)

    #Finds and processes books in the books folder

    new_book_files = misc.find_unproccessed_files()

    if len(new_book_files) != 0:
        new_book_file_names = ', '.join(new_book_files).replace('_', ' ').replace(f'.{book_ext}','').title()

        if len(new_book_files) == 1:
            permission = user_input.user_input(f"New book detected: {new_book_file_names}. Embed?", bool)
        else:
            permission = user_input.user_input(f"New books detected: {new_book_file_names}. Embed?", bool)

        if permission == True:
            for file_name in new_book_files:
                new_embedding = embed.new_embedding(file_name)
                misc.save_file(new_embedding, file_name.split(".")[0])

    #Import system prompts from prompts.txt

    system_prompts = {}
    with open("prompts.txt", "r") as prompts:
        for prompt in prompts:
            stripped_prompt = prompt.strip()
            if stripped_prompt:
                name, text = stripped_prompt.split(' = ')
                system_prompts[name] = text

    #Loads embed files to save_data_cache

    embed_file_list = glob.glob(os.path.join(embed_folder, f'*.{embed_ext}'))

    if len(embed_file_list) == 0:
        input("No books detected. Download markup files from New Christian Bible Study and put them in the 'books' folder. Alternatively, message me for an email of the files.")
        exit()

    #On first boot, runs a test to find an appropriate thread count

    max_workers = int(os.environ.get("load_threads") or 0)
    if max_workers == 0:
        max_workers = multi_threading.multi_thread_test(build_save_data_cache,max_workers,embed_file_list)
    
    save_data_cache = build_save_data_cache(max_workers, embed_file_list)
    
    return save_data_cache, system_prompts

def build_save_data_cache(max_workers, embed_file_list):
    save_data_cache = {
        "chunks" : [],
        "embeds" : [],
        "ref" : [],
    }
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(misc.load_embedded_file,embed_file_list), total=len(embed_file_list), desc=f"Loading Books ({max_workers} threads)"))
        for result in results:
            save_data_cache = misc.combine_similar_dict(save_data_cache, result)
    return save_data_cache
