import math
import re
from tqdm import tqdm
from scripts import misc
from scripts import formatting
from scripts.config import config
from typing import Tuple, Dict
import os
import openai



#Takes a book text file and embeds them into the "save_data" dictionary

def chunk_and_embed(text: str, book_name) -> dict:
    data = {
    "chunks" : [], #Chunks are books broken into pieces, bite sized things that ChatGPT can utilize.
    "embeds" : [], #Embeddings are vector data for sections of text. The closer together in space two vectors are, the more similar the text is in terms of content.
    "ref" : [], #Stores reference information (ie "Heaven and Hell 403")
    }

    data["ref"], data["chunks"] = chunk_text_by_format(text, book_name)
    data["ref"], data["chunks"] = find_and_split_large_chunks(data["ref"], data["chunks"])
    total_chunks = len(data["chunks"])
    for i in tqdm (range(total_chunks), desc=f"Embedding {book_name}"):
        new_embed = create_embedding(data["chunks"][i])
        data["embeds"].append(new_embed)
    return data

def chunk_text_by_format(text: str, book_name: str) -> Tuple[Dict, Dict]:
    markups = {
        'ncbs' : re.compile(r'\d+#pid#'),
        'bible' : "Genesis"
    }
    first_line = re.split("\n", text)[0].strip().lstrip('\ufeff')
    if markups["ncbs"].match(first_line):
        references, content = formatting.ncbs(text, book_name)
    elif first_line.startswith(markups["bible"]):
        references, content = formatting.bible(text, book_name)
    return references, content

#Loads and chunks text.

def find_and_split_large_chunks(references_raw, content_raw):

    chunk_indicator = "\n"
    references = []
    content = []
    
    max_tokens = int(config.get('embedding', 'max_tokens_in_chunks'))

    for i, chunk in enumerate(content_raw):
        chunk_tokens = misc.count_tokens(chunk)
        if chunk_tokens > max_tokens:
            chunk_split = split_chunk(chunk, chunk_indicator)
            for splinter in chunk_split:
                content.append(splinter)
                references.append(references_raw[i])
        else:
            content.append(chunk)
            references.append(references_raw[i])
    
    return references, content

#Splits a string evenly into a list of chunks, with none being higher than the constant "MAX_TOKENS_IN_CHUNKS"

def split_chunk(string: str, chunk_indicator: str):
    max_tokens = int(config.get('embedding', 'max_tokens_in_chunks'))
    num_tokens_in_string = misc.count_tokens(string)
    return_length = math.ceil(num_tokens_in_string/max_tokens)

    avg_token_per_return_item = num_tokens_in_string/return_length

    sentences = string.split(chunk_indicator)
    sentences = list(filter(lambda x: x != "", sentences))

    return_list = [""]

    tokens_in_chunk = 0 #Once this hits the constant 'MAX_TOKENS_IN_CHUNKS' , it loops back to zero and starts a new chunk.

    for i, item in enumerate(sentences):
        num_tokens_in_sentence = misc.count_tokens(item)
        if tokens_in_chunk + num_tokens_in_sentence > avg_token_per_return_item:
            if tokens_in_chunk + num_tokens_in_sentence < max_tokens and len(return_list) < return_length:
                return_list.append(item)
            else:
                return_list[-1] += item
                return_list.append("")
            tokens_in_chunk = 0
        else:
            return_list[-1] += item
            tokens_in_chunk = misc.count_tokens(return_list[-1])
    
    return return_list

#Creates a readable book name from the name of the file.

def book_title_from_file_name(file_directory):
    file_name = os.path.basename(file_directory)
    file_name_without_ext = os.path.splitext(file_name)[0]
    book_name = file_name_without_ext.replace("_", " ").title() #Removes underscores and makes the first letter uppercase
    book_name = re.sub(r'\[.*?\]', '', book_name).strip() #Removes anything in brackets.
    return book_name

#Gets the embedding value of a piece of text

def create_embedding(text: str):
    model = config.get('openai_properties','embed_model')
    embedding = openai.Embedding.create(
        input=text,
        model=model,
    )
    embed_vector = embedding["data"][0]["embedding"]
    return embed_vector

#Compares the search term to all embeds in a list, and retruns the embedded data sorted

def find_relevant_embeddings(search_term: str, embed_data: list):
    user_question_vector = create_embedding(search_term)
    embed_similarity = misc.vector_similarity(user_question_vector, embed_data["embeds"])
    embeds_chunk_tuples = list(zip(embed_data["chunks"],embed_similarity, embed_data["ref"]))
    sorted_results = sorted(embeds_chunk_tuples, key=lambda x: x[1], reverse=True)
    return sorted_results

def embed_file_list(file_list, embed_ext, embed_dir):
    for file_name in file_list:
        txt_file_string = misc.txt_file_to_string(file_name)
        book_title = book_title_from_file_name(file_name)
        new_embedding = chunk_and_embed(txt_file_string, book_title)
        misc.save_file_pickle(new_embedding, file_name.split(".")[0], embed_ext, embed_dir)
