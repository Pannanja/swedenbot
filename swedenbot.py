from dotenv import load_dotenv
import glob
import gzip
import json
import math
import numpy
import openai
import os
import pickle
import re
import tiktoken
from tqdm import tqdm

MAX_TOKENS_IN_CHUNKS = 820
TOKENS_IN_SYSTEM_PROMPT = 4096/2
TOKEN_MODEL = "gpt-3.5-turbo"
EMBED_MODEL = "text-embedding-ada-002"
TEMPERATURE = 0.8 #Creativity of the AI
TEXT_ENCODING = "utf-8"

BOOKS_FOLDER = "books"
DATA_FOLDER = "data"

QUERY_BOT_ENABLED = True #Query bot is ChatGPT geared toward rewriting the prompt for better search accuraccy.

book_save_data = {
    "chunks" : [], #Chunks are books broken into pieces, bite sized things that ChatGPT can utilize.
    "embeds" : [], #Embeddings are vector data for sections of text. The closer together in space two vectors are, the more similar the text is in terms of content.
    "ref" : [], #Stores reference information (ie "Heaven and Hell 403")
}

#Gets the embedding value of a piece of text

def get_embedding(text: str):
    embedding = openai.Embedding.create(
        input=text,
        model=EMBED_MODEL,
    )
    return embedding["data"][0]["embedding"]

#Counts tokens in input

def token_count(text: str):
    encoding_model = tiktoken.encoding_for_model(TOKEN_MODEL)
    return len(encoding_model.encode(text))

#Splits a string evenly into a list of chunks, with none being higher than the constant "MAX_TOKENS_IN_CHUNKS"

def split_string_into_chunks(string: str, seperator: str):
    num_tokens_in_string = token_count(string)
    return_length = math.ceil(num_tokens_in_string/MAX_TOKENS_IN_CHUNKS)

    avg_token_per_return_item = num_tokens_in_string/return_length

    sentences = string.split(seperator)
    return_list = [""]
    tokens_in_chunk = 0 #Once this hits the constant 'MAX_TOKENS_IN_CHUNKS' , it loops back to zero and starts a new chunk.

    for i, item in enumerate(sentences):
        num_tokens_in_sentence = token_count(item)
        if tokens_in_chunk + num_tokens_in_sentence > avg_token_per_return_item:
            if tokens_in_chunk + num_tokens_in_sentence < MAX_TOKENS_IN_CHUNKS and len(return_list) < return_length:
                return_list.append(item)
            else:
                return_list[-1] += item
                return_list.append("")
            tokens_in_chunk = 0
        else:
            return_list[-1] += item
            tokens_in_chunk = token_count(return_list[-1])
    
    return return_list

#Creates a readable book name from the name of the file.

def name_book(file_name):
    book_name = file_name.replace("_", " ").title() #Removes underscores and makes the first letter uppercase
    book_name = re.sub(r'\[.*?\]', '', book_name).strip() #Removes anything in brackets.
    return book_name

#Loads and chunks text. Currently only works with NCBS markups.

def chunk_text_from_file(file_name):

    book_name = name_book(file_name)

    file = open(f"{BOOKS_FOLDER}/{file_name}.txt", encoding=TEXT_ENCODING)
    text = file.read()
    file.close()

    references_raw, content_raw = format_text_from_ncbs(text,book_name)

    references = []
    content = []

    #splits chunks that are too large, and appends them all to the new references and content lists.
    for i, chunk in enumerate(content_raw):
        chunk_tokens = token_count(chunk)
        if chunk_tokens > MAX_TOKENS_IN_CHUNKS:
            chunk_split = split_string_into_chunks(chunk, "\n\n")
            for splinter in chunk_split:
                content.append(splinter)
                references.append(references_raw[i])
        else:
            content.append(chunk)
            references.append(references_raw[i])
    
    return content, references

#NCBS text formatting

def format_text_from_ncbs(text, book_name):

    markup_new_section = r'ppp\d+#pid#\d+.'
    markup_new_section_short = "#pid#"
    markup_new_subsection = r'ttt\[\d+\] '
    markup_bible_verse = 'bbb'
    markup_bible_verse_2 = 'bbbccc'
    markup_bible_verse_3 = 'ccc'
    markup_unknown = r"`fff\d+`"
    markup_unknown_2 = "`qqq`"
    markup_unknown_3 = "@@@"

    def clean(): #Removes formatting
        content[-1] = content[-1].replace(markup_unknown_3,"")
        content[-1] = content[-1].replace(markup_bible_verse,":")
        content[-1] = content[-1].replace(markup_bible_verse_2,":")
        content[-1] = content[-1].replace(markup_bible_verse_3,":")
        content[-1] = content[-1].replace(markup_unknown_2,"")
        content[-1] = content[-1].replace(markup_unknown_3,"")
        #content[-1] = re.sub(markup_new_section[:-1],"",content[-1])
        content[-1] = re.sub(markup_new_section,"",content[-1])
        content[-1] = re.sub(markup_new_subsection,"",content[-1])

    references = [""]
    content = [""]

    reference_markup = ""
    subsection_number = "ttt[1]" #Defaults to [1] when a new section starts

    text_file_lines = re.split("\n\n", text)


    #Content formatting, (reference gets formatted a little)

    for i, line in enumerate(text_file_lines):

        #Checks for new section

        if re.search(markup_new_section, line):
            subsection_number = "ttt[1]"

            reference_markup = re.search(markup_new_section, line).group()
            references.append(reference_markup[:-1] + subsection_number)

            content.append(line)
        
        #Checks for new subsection

        elif re.search(markup_new_subsection, line):
            subsection_number = re.search(markup_new_subsection, line).group()

            references.append(reference_markup[:-1] + subsection_number)

            content.append(line)
        
        else:
            content[-1] += "\n\n" + line
        
        clean()

                    

    #Reference formatting

    for i, item in enumerate(references):

        reference_pid = references[i].find(markup_new_section_short)
        if reference_pid != -1:
            references[i] = references[i][reference_pid+len(markup_new_section_short):]
        
        references[i] = references[i].replace("ttt","")

        references[i] = book_name + " " + references[i]

    return references, content

#Takes a book text file in the NCBS formatting and embeds them into the "save_data" dictionary

def new_embedding(document_name):

    book_save_data["chunks"], book_save_data["ref"] = chunk_text_from_file(document_name)

    book_save_data["embeds"] = []
    total_chunks = len(book_save_data["chunks"])

    for i in tqdm (range(total_chunks), desc=f"Embedding {document_name}"):
        new_embed = get_embedding(book_save_data["chunks"][i])
        book_save_data["embeds"].append(new_embed)

#Loads pre-made embeddings in the data folder.

def load_embedding():
    global book_save_data
    book_save_data = {
        "chunks" : [],
        "embeds" : [], 
        "ref" : [], 
    }
    file_path = glob.glob(f"{DATA_FOLDER}/*.embed")
    for file in file_path:
        print(f"found file {file}")
        with gzip.open(file, 'rb') as f:
            temp_save_data = pickle.load(f)
            book_save_data["chunks"].extend(temp_save_data["chunks"])
            book_save_data["embeds"].extend(temp_save_data["embeds"])
            book_save_data["ref"].extend(temp_save_data["ref"])

#Checks how similar two vectors are, spits out a number between 0 and 1

def vector_similarity(question, vectors):
    vector_similarity_list = []
    for item in vectors:
        result = numpy.dot(numpy.array(question),numpy.array(item))
        vector_similarity_list.append(result)
    return vector_similarity_list

#Checks for books that are in the "books" folder, finds which aren't already embedded in the "data" folder, then asks permission to embed new books.

def check_for_new_books():

    file_path_embed = glob.glob(f"data/*.embed")
    file_path_book = glob.glob(f"books/*.txt")

    file_names_embed = []
    file_names_book = []

    for file in file_path_embed:
        file_names_embed.append(os.path.basename(file).split(".")[0])
    for file in file_path_book:
        file_names_book.append(os.path.basename(file).split(".")[0])
    
    new_document_names_list = [item for item in file_names_book if item not in file_names_embed]

    if len(new_document_names_list) != 0:
        new_books_names = ', '.join(new_document_names_list).replace('_', ' ').title()

        if len(new_document_names_list) == 1:
            user_input = input(f"New book detected: {new_books_names}. Embed? Y/N: ")
        else:
            user_input = input(f"New books detected: {new_books_names}. Embed? Y/N: ")
        
        if user_input.lower() == "y":
            for document_name in new_document_names_list:
                new_embedding(document_name)
                with gzip.open(f'data/{document_name}.embed', 'wb') as handle:
                    pickle.dump(book_save_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
#Asks ChatGPT a question

def ask_question(question):
    if QUERY_BOT_ENABLED:
        query_bot_response = query_bot(question).replace('[','').replace(']','')
        user_question_vector = get_embedding(query_bot_response)
    else:
        user_question_vector = get_embedding(question)

    embed_similarity = vector_similarity(user_question_vector,book_save_data["embeds"])

    system_prompt = "You are 'Swedenbot', a chatbot that answers questions about what Emanuel Swedenborg wrote in his books. The user will ask a question, and you must answer it using the context below and your existing knowledge about his writings. Give a detailed answer. If the answer is not contained within the context, say 'Sorry, I'm not sure'. You may fulfill users creative requests, like writing a song or writing in another style. \n\nContext from Swedenborg's writings:\n"
    
    embeds_chunk_tuples = list(zip(book_save_data["chunks"],embed_similarity, book_save_data["ref"]))
    sorted_results = sorted(embeds_chunk_tuples, key=lambda x: x[1], reverse=True)

    total_tokens = token_count(system_prompt)
    prompts = 0   

    while total_tokens < TOKENS_IN_SYSTEM_PROMPT:
        tokens_in_next_prompt = token_count(sorted_results[prompts][0])
        total_tokens += tokens_in_next_prompt
        if total_tokens < TOKENS_IN_SYSTEM_PROMPT:
            prompts +=1


    relevant_results = [t[0] for t in sorted_results[:prompts]]
    relevant_embeds = [t[1] for t in sorted_results[:prompts]]
    relevant_ref = [t[2] for t in sorted_results[:prompts]]

    #Creates message history
    relevant_results_string = ''
    relevant_results_string_trunc = ''
    for i in range(len(relevant_results)):
        relevant_results_string += relevant_ref[i] + ': ' + relevant_results[i] + '\n\n'
    for i in range(len(relevant_results)):
        results = relevant_results[i][:150].replace('\n', " ").strip()
        relevant_results_string_trunc += relevant_ref[i][:-1] + ': [' + str(round(relevant_embeds[i]*100, 2)) + "%]\n" + results + '...\n\n'

    message_history = []
    message_history.append({"role":"system", "content": system_prompt + relevant_results_string})

    message_history.append({"role":"user", "content": user_question})

    #Runs ChatGPT

    chatGPT = openai.ChatCompletion.create(
        model=TOKEN_MODEL,
        messages=message_history,
        temperature=TEMPERATURE,
        stream=True
    )
    gpt_reply = ""

    #Streams the response, so you can see it as it comes in.

    for message in chatGPT:
        json_response = json.loads(str(message))
        try:
            word = json_response['choices'][0]['delta']['content']
            gpt_reply += word
            print(word, end="", flush=True)
        except Exception as e:
            pass

    print("\n")
    print(relevant_results_string_trunc)
    return(message_history)

#Formats the query better for search terms. Disable by

def query_bot(question):

    message_history = []
    message_history.append({"role":"system", "content": "You are 'swedenborg_query_bot'. The user will supply a query about Swedenborg, and you will respond with search terms in brackets that you'd like to use to search Swedenborg's writings to help you formulate your response. Your response should only contain search terms for Swedenborg's writings and not answers or explanations. Do not add any additional information or context beyond the search terms. Only search for content that will assist you in formulating your response. Strip away any text that is unrelated to the query, such as instructions on how to respond (in a poem, like a child, etc.). Only respond with one bracket, and keep it extremely brief. Here are a few examples to illustrate the format of the prompt, with the query in (parentheses) and your response in [brackets]:\n\n(What is regeneration? Explain like you're a cat.) [regeneration]\n(Are there babies in heaven?) [babies in heaven]\n(Write a poem about divine providence) [divine providence]\n(Why do we age? It's so painful) [Why age painful]\n(Write a poem about the dying process in iambic parameter.) [dying process]\n(Write a poem without the letter 'e' about clothes in heaven) [clothes heaven]\n(Write a poem about working in heaven) [working in heaven]\n(Are there gay people in heaven? Because I am gay.) [gay people heaven]\n(Write a poem about regeneration, in the style of a salty sea captain) [regeneration]\n(Write a poem about regeneration, in the style of Donald Trump) [regeneration]\n(Write a theme song for moon spirits)[moon spirits]\n(Explain swedenborg's concept of 'ruling love' using hearthstone terms)[ruling love]"})
    message_history.append({"role":"user", "content": question})

    chatGPT = openai.ChatCompletion.create(
        model=TOKEN_MODEL,
        messages=message_history,
        temperature=TEMPERATURE,
        stream=True
    )

    gpt_reply = ""

    #Streams the response, so you can see it as it comes in.

    for message in chatGPT:
        json_response = json.loads(str(message))
        try:
            word = json_response['choices'][0]['delta']['content']
            gpt_reply += word
            print(word, end="", flush=True)
        except Exception as e:
            pass

    print("\n")
    return gpt_reply

#-------------------------------------------CODE START

load_dotenv()
openai.api_key = os.environ.get("api-token")
if openai.api_key == None:
    print("No API key detected. Create a .env file in the same folder as this, and put in it api-token = 'insert token here'. You get your token from https://platform.openai.com/")
    exit()
check_for_new_books()
load_embedding()
while True:
    user_question = input("Ask Question: ")
    ask_question(user_question)