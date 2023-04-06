import glob
import gzip
import numpy
import openai
import os
import pickle
import tiktoken

TOKEN_MODEL = "gpt-3.5-turbo"

#Gets the embedding value of a piece of text

def get_embedding(text: str, embed_model: str):
    embedding = openai.Embedding.create(
        input=text,
        model=embed_model,
    )
    return embedding["data"][0]["embedding"]

#Counts tokens in input

def token_count(text: str):
    encoding_model = tiktoken.encoding_for_model(TOKEN_MODEL)
    return len(encoding_model.encode(text))

#Checks how similar two vectors are, spits out a number between 0 and 1

def vector_similarity(question, vectors):
    vector_similarity_list = []
    for item in vectors:
        result = numpy.dot(numpy.array(question),numpy.array(item))
        vector_similarity_list.append(result)
    return vector_similarity_list

#Compares two lists of files, and returns the ones in the second one not in the first

def find_unproccessed_files(unprocessed_folder: str, processed_folder: str):
    processed_files = {os.path.basename(file).split(".")[0] for file in glob.glob(f"{processed_folder}/*.*")}
    unprocessed_files = {os.path.basename(file).split(".")[0] for file in glob.glob(f"{unprocessed_folder}/*.*")}
    new_unprocessed_files = list(unprocessed_files - processed_files)
    return new_unprocessed_files

#Saves embeds

def save_file(data, file_name: str, save_folder: str, extension: str):
    with gzip.open(f'{save_folder}/{file_name}.{extension}', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

