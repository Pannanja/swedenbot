#Standard Libraries
import os
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv, set_key

#Third Party Libraries
import glob
import openai
from tqdm import tqdm
import pinecone

#Local Imports
from scripts import embed
from scripts import misc
from scripts import user_input
from scripts.config import config

load_dotenv()

def load_api_key_open_ai():
    openai_api_key = os.environ.get("api-key")
    if openai_api_key == None:
        openai_api_key = user_input.user_input("Enter OpenAI API key",str)
        set_key(".env","api-key",openai_api_key)
    openai.api_key = openai_api_key

def load_api_key_pinecone():
    pinecone_api_key = os.environ.get("pinecone-api-key")
    pinecone.init(api_key=pinecone_api_key)
    pinecone.init

def combine_pickle_file_data(max_workers: int, embed_file_list: list) -> Dict[str, str]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(misc.load_file_pickle,embed_file_list),
                            total=len(embed_file_list), 
                            desc=f"Loading Books ({max_workers} threads)"))
        save_data_cache = results[0]
        save_data_cache = {key: [] for key in save_data_cache.keys()}
        for result in results:
            save_data_cache = misc.combine_similar_dict(save_data_cache, result)
    return save_data_cache

def process_new_books(book_dir, book_ext, embed_dir, embed_ext):
    new_book_files = misc.find_unprocessed_files(book_dir, book_ext, embed_dir, embed_ext)
    if len(new_book_files) != 0:
        new_book_file_names = ', '.join(os.path.split(file)[-1].replace('_', ' ').replace(f'.{book_ext}', '').title() for file in new_book_files)
        if len(new_book_files) == 1:
            permission = user_input.user_input(f"New book detected: {new_book_file_names}. Embed?", bool)
        else:
            permission = user_input.user_input(f"New books detected: {new_book_file_names}. Embed?", bool)
        if permission == True:
            embed.embed_file_list(new_book_files, embed_ext, embed_dir)

def load_embed_files(embed_file_list):
    if len(embed_file_list) == 0:
        input("No books detected. Download markup files from New Christian Bible Study and put them in the 'books' folder. Alternatively, message me for an email of the files.")
        exit()
    
    load_cpu_threads = int(os.environ.get("load_cpu_threads") or 4)
    #load_cpu_threads = int(os.environ.get("load_cpu_threads") or 0)
    #if load_cpu_threads == 0:
    #    load_cpu_threads = multi_threading.multi_thread_test(build_save_data_cache,load_cpu_threads,embed_file_list)
    
    save_data_cache = combine_pickle_file_data(load_cpu_threads, embed_file_list)
    return save_data_cache


def init_swedenbot() -> Dict[str,str]:
    load_api_key_open_ai()
    #load_api_key_pinecone()

    #Checks for new books, and asks the user if they'd like to embed.
    book_dir = config.get('data','books_directory')
    book_ext = config.get('data','book_ext')
    embed_dir = config.get('data','embed_directory')
    embed_ext = config.get('data','embed_ext')
    process_new_books(book_dir, book_ext, embed_dir, embed_ext)

    #Loads embed files to save_data_cache
    embed_file_list = glob.glob(os.path.join(embed_dir, f'*.{embed_ext}'))
    save_data_cache = load_embed_files(embed_file_list)

    return save_data_cache



    

