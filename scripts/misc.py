from scripts.config import config
import glob
import gzip
import numpy
import openai
import os
import pickle
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv, set_key
from scripts import multi_threading





#Gets the embedding value of a piece of text

def get_embedding(text: str):
    model = config.get('openai_properties','embed_model')
    embedding = openai.Embedding.create(
        input=text,
        model=model,
    )
    return embedding["data"][0]["embedding"]

#Counts tokens in input

def token_count(text: str):
    token_model = config.get('openai_properties','token_model')
    encoding_model = tiktoken.encoding_for_model(token_model)
    return len(encoding_model.encode(text))

#Checks how similar two vectors are, spits out a number between 0 and 1

def vector_similarity(question, vectors):
    question_np = numpy.asarray(question)
    vectors_np = numpy.asarray(vectors)
    vector_similarity_list = numpy.dot(vectors_np, question_np)
    return vector_similarity_list

#Compares two lists of files, and returns the ones in the second one not in the first

def find_unproccessed_files():
    embed_folder = config.get('data','embed_folder')
    books_folder = config.get('data','books_folder')
    processed_files = {os.path.basename(file).split(".")[0] for file in glob.glob(f"{embed_folder}/*.*")}
    unprocessed_files = {os.path.basename(file).split(".")[0] for file in glob.glob(f"{books_folder}/*.*")}
    new_unprocessed_files = list(unprocessed_files - processed_files)
    return new_unprocessed_files

#Saves embeds

def save_file(data, file_name: str):
    save_folder = config.get('data','embed_folder')
    extension = config.get('data','embed_ext')
    with gzip.open(f'{save_folder}/{file_name}.{extension}', 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

#Loads Embeds

def load_embedded_file(embed_file):
    with gzip.open(embed_file, 'rb') as file:
        temp_save_data = pickle.load(file)
    return temp_save_data

#Compares the search term to all embeds in a list, and retruns the embedded data sorted

def find_relevant_embeds(search_term: str, embed_data: list):
    user_question_vector = get_embedding(search_term)
    embed_similarity = vector_similarity(user_question_vector, embed_data["embeds"])
    embeds_chunk_tuples = list(zip(embed_data["chunks"],embed_similarity, embed_data["ref"]))
    sorted_results = sorted(embeds_chunk_tuples, key=lambda x: x[1], reverse=True)
    return sorted_results

#Formats references and appends them to the end of a string (usually a system prompt). It also returns a truncated version, to save space.

def append_embeds(sorted_embeds: list, system_prompt: str):
    max_tokens_in_system_prompt = config.getint('openai_properties','max_tokens_in_system_prompt')
    total_tokens = token_count(system_prompt)
    prompts = 0
    while total_tokens < max_tokens_in_system_prompt:
        tokens_in_next_prompt = token_count(sorted_embeds[prompts][0])
        total_tokens += tokens_in_next_prompt
        if total_tokens < max_tokens_in_system_prompt:
            prompts +=1
    relevant_content = [t[0] for t in sorted_embeds[:prompts]]
    relevant_ref = [t[2] for t in sorted_embeds[:prompts]]

    relevant_results_string = ''
    relevant_results_string_trunc = ''
    source_character_limit = int(config.get('chatbot','source_character_limit'))

    for i in range(len(relevant_content)):
        reference = f"{relevant_ref[i][0]} {relevant_ref[i][1]}[{relevant_ref[i][2]}]"
        relevant_results_string += f"{reference}: {relevant_content[i]} + '\n\n'"
        trunc_content = relevant_content[i][:source_character_limit].replace('\n', " ").strip()
        relevant_results_string_trunc += f"{reference}\n{trunc_content}...\n"

    system_prompt_with_embeds = system_prompt + relevant_results_string
    return system_prompt_with_embeds, relevant_results_string_trunc

def combine_similar_dict(dict_a, dict_b):
    for key in dict_a:
        dict_a[key].extend(dict_b[key])
    return dict_a