from scripts.config import config
import glob
import gzip
import numpy
import os
import pickle
import tiktoken

#Counts tokens in input

def count_tokens(text: str):
    token_model = config.get('openai_properties','token_model')
    encoding_model = tiktoken.encoding_for_model(token_model)
    token_count = len(encoding_model.encode(text))
    return token_count

#Checks how similar two vectors are, spits out a number between 0 and 1

def vector_similarity(question, vectors):
    question_np = numpy.asarray(question)
    vectors_np = numpy.asarray(vectors)
    vector_similarity_list = numpy.dot(vectors_np, question_np)
    return vector_similarity_list

#Compares two lists of files, and returns the ones in the second one not in the first

def find_unprocessed_files(source_directory, source_extension, processed_directory, processed_extension):
    processed_files = glob.glob(f"{processed_directory}/*.{processed_extension}")
    processed_file_names = {os.path.basename(file).split(".")[0] for file in processed_files}
    unprocessed_files = glob.glob(f"{source_directory}/*.{source_extension}")
    unprocessed_file_names = {file for file in unprocessed_files if os.path.basename(file).split(".")[0] not in processed_file_names}
    return list(unprocessed_file_names)

#Saves embeds

def save_file_pickle(data, file_name: str, extension: str, save_directory: str):
    file_name = os.path.basename(file_name)
    with gzip.open(f'{save_directory}/{file_name}.{extension}', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

#Loads Embeds

def load_file_pickle(embed_file):
    with gzip.open(embed_file, 'rb') as file:
        temp_save_data = pickle.load(file)
    return temp_save_data

def combine_similar_dict(dict_a, dict_b):
    for key in dict_a:
        dict_a[key].extend(dict_b[key])
    return dict_a

def txt_file_to_string(txt_file_directory: str) -> str:
    with open(txt_file_directory, encoding="utf-8") as file:
        text_string = file.read()
    return text_string