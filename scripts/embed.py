import math
import re
from tqdm import tqdm
from scripts import misc
from scripts import formatting

MAX_TOKENS_IN_CHUNKS = 820
TEXT_ENCODING = "utf-8"
EMBEDDING_FORMATTING = "ncbs"

BOOKS_FOLDER = "books"


book_save_data = {
    "chunks" : [], #Chunks are books broken into pieces, bite sized things that ChatGPT can utilize.
    "embeds" : [], #Embeddings are vector data for sections of text. The closer together in space two vectors are, the more similar the text is in terms of content.
    "ref" : [], #Stores reference information (ie "Heaven and Hell 403")
}

#Takes a book text file and embeds them into the "save_data" dictionary

def new_embedding(document_name, embed_model):

    book_save_data["chunks"], book_save_data["ref"] = chunk_text_from_file(document_name)

    book_save_data["embeds"] = []
    total_chunks = len(book_save_data["chunks"])

    for i in tqdm (range(total_chunks), desc=f"Embedding {document_name}"):
        new_embed = misc.get_embedding(book_save_data["chunks"][i], embed_model)
        book_save_data["embeds"].append(new_embed)
    return book_save_data

#Loads and chunks text. Currently only works with NCBS markups.

def chunk_text_from_file(file_name):

    book_name = name_book(file_name)

    file = open(f"{BOOKS_FOLDER}/{file_name}.txt", encoding=TEXT_ENCODING)
    text = file.read()
    file.close()

    references_raw, content_raw = formatting.format_text(text,book_name)

    references = []
    content = []

    #splits chunks that are too large, and appends them all to the new references and content lists.
    for i, chunk in enumerate(content_raw):
        chunk_tokens = misc.token_count(chunk)
        if chunk_tokens > MAX_TOKENS_IN_CHUNKS:
            chunk_split = split_string_into_chunks(chunk, "\n\n")
            for splinter in chunk_split:
                content.append(splinter)
                references.append(references_raw[i])
        else:
            content.append(chunk)
            references.append(references_raw[i])
    
    return content, references


#Splits a string evenly into a list of chunks, with none being higher than the constant "MAX_TOKENS_IN_CHUNKS"

def split_string_into_chunks(string: str, seperator: str):
    num_tokens_in_string = misc.token_count(string)
    return_length = math.ceil(num_tokens_in_string/MAX_TOKENS_IN_CHUNKS)

    avg_token_per_return_item = num_tokens_in_string/return_length

    sentences = string.split(seperator)
    return_list = [""]
    tokens_in_chunk = 0 #Once this hits the constant 'MAX_TOKENS_IN_CHUNKS' , it loops back to zero and starts a new chunk.

    for i, item in enumerate(sentences):
        num_tokens_in_sentence = misc.token_count(item)
        if tokens_in_chunk + num_tokens_in_sentence > avg_token_per_return_item:
            if tokens_in_chunk + num_tokens_in_sentence < MAX_TOKENS_IN_CHUNKS and len(return_list) < return_length:
                return_list.append(item)
            else:
                return_list[-1] += item
                return_list.append("")
            tokens_in_chunk = 0
        else:
            return_list[-1] += item
            tokens_in_chunk = misc.token_count(return_list[-1])
    
    return return_list

#Creates a readable book name from the name of the file.

def name_book(file_name):
    book_name = file_name.replace("_", " ").title() #Removes underscores and makes the first letter uppercase
    book_name = re.sub(r'\[.*?\]', '', book_name).strip() #Removes anything in brackets.
    return book_name