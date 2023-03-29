from dotenv import load_dotenv
import glob
import gzip
import json
import openai
import os
import pickle
from tqdm import tqdm
from scripts import embed
from scripts import misc

TOKENS_IN_SYSTEM_PROMPT = 4096/2
TOKEN_MODEL = "gpt-3.5-turbo"
EMBED_MODEL = "text-embedding-ada-002"

BOOKS_FOLDER = "books"
DATA_FOLDER = "data"

QUERY_REWRITE_ENABLED = True #Query rewrite is ChatGPT geared toward rewriting the prompt for better search accuraccy.
QUERY_REWRITE_INSTANCES = 5
TEMPERATURE = 0.8 #Creativity of the AI


book_save_data = {
    "chunks" : [], #Chunks are books broken into pieces, bite sized things that ChatGPT can utilize.
    "embeds" : [], #Embeddings are vector data for sections of text. The closer together in space two vectors are, the more similar the text is in terms of content.
    "ref" : [], #Stores reference information (ie "Heaven and Hell 403")
}


#Loads pre-made embeddings in the data folder.

def load_embedding():
    global book_save_data
    book_save_data = {
        "chunks" : [],
        "embeds" : [], 
        "ref" : [], 
    }
    file_path = glob.glob(f"{DATA_FOLDER}/*.embed")
    if len(file_path) == 0:
        input("No books detected. Download markup files from New Christian Bible Study and put them in the 'books' folder. Alternatively, message me for an email of the files.")
        exit()
    for i in tqdm(range(len(file_path)), desc="Loading Books"):
        with gzip.open(file_path[i], 'rb') as f:
            temp_save_data = pickle.load(f)
            book_save_data["chunks"].extend(temp_save_data["chunks"])
            book_save_data["embeds"].extend(temp_save_data["embeds"])
            book_save_data["ref"].extend(temp_save_data["ref"])

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
                book_save_data = embed.new_embedding(document_name, EMBED_MODEL)
                with gzip.open(f'data/{document_name}.embed', 'wb') as handle:
                    pickle.dump(book_save_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
#Asks ChatGPT a question

def gtp_main(question):
    if QUERY_REWRITE_ENABLED:
        query_bot_response = gtp_query_rewrite(question)
        user_question_vector = misc.get_embedding(query_bot_response, EMBED_MODEL)
    else:
        user_question_vector = misc.get_embedding(question, EMBED_MODEL)

    embed_similarity = misc.vector_similarity(user_question_vector,book_save_data["embeds"])

    system_prompt = "You are 'Swedenbot', a chatbot that answers questions about what Emanuel Swedenborg wrote in his books. The user will ask a question, and you must answer it using the context below. Give a detailed answer. If the answer is not contained within the context, say 'Sorry, I'm not sure'. You may fulfill users creative requests, like writing a song or writing in another style. Do not respond with information irrelevant to the user question, even if it's in the context.\n\nContext from Swedenborg's writings:\n"
    
    embeds_chunk_tuples = list(zip(book_save_data["chunks"],embed_similarity, book_save_data["ref"]))
    sorted_results = sorted(embeds_chunk_tuples, key=lambda x: x[1], reverse=True)

    total_tokens = misc.token_count(system_prompt)
    prompts = 0   

    while total_tokens < TOKENS_IN_SYSTEM_PROMPT:
        tokens_in_next_prompt = misc.token_count(sorted_results[prompts][0])
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
        relevant_results_string_trunc += relevant_ref[i][:-1] + ': [' + str(round(relevant_embeds[i]*100, 2)) + "%]\n" + results + '...\n'

    message_history = []
    message_history.append({"role":"system", "content": system_prompt + relevant_results_string})

    message_history.append({"role":"user", "content": question})

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

    print("\n\nSOURCES:")
    print(relevant_results_string_trunc)
    return(message_history)

#Formats the query better for search terms. Disable by

def gtp_query_rewrite(question):

    message_history = []
    message_history.append({"role":"system", "content": f"You are 'swedenborg_query_bot'. The user will supply a query about Swedenborg, and you will respond with search terms in brackets that you'd like to use to search Swedenborg's writings to help you formulate your response. Choose up to {QUERY_REWRITE_INSTANCES} unique search terms, each in seperate brackets. Don't search for terms that are completely unrelated to Swedenborg. Your response should only contain search terms. Strip away any text that is unrelated to the query, such as instructions on how to respond or what method of describing to use (in a poem, like a child, using terms from harry potter etc.). Here are a few examples to illustrate the format of the prompt, with the query in (parentheses) and your response in [brackets]:\n\n(What is regeneration? Explain like you're a cat.) [regeneration]\n(Are there babies in heaven?) [babies in heaven]\n(Write a poem about divine providence) [divine providence]\n(Why do we age? It's so painful) [Why age painful]\n(Write a poem about the dying process in iambic parameter.) [dying process]\n(Write a poem without the letter 'e' about clothes in heaven) [clothes heaven]\n(Write a poem about working in heaven) [working in heaven]\n(Are there gay people in heaven? Because I am gay.) [gay people heaven]\n(Write a poem about regeneration, in the style of a salty sea captain) [regeneration]\n(Write a poem about regeneration, in the style of Donald Trump) [regeneration]\n(Write a theme song for moon spirits)[moon spirits]\n(Explain swedenborg's concept of 'ruling love' using hearthstone terms)[ruling love]\n(Explain heaven using analogies from harry potter)[heaven]"})
    message_history.append({"role":"user", "content": question})

    chatGPT = openai.ChatCompletion.create(
        model=TOKEN_MODEL,
        messages=message_history,
        temperature=TEMPERATURE,
    )

    reply_content = chatGPT.choices[0].message.content
    print(f"\nSearching: {reply_content}\n")

    return reply_content

#-------------------------------------------CODE START

load_dotenv()
openai.api_key = os.environ.get("api-token")
if openai.api_key == None:
    input("No API key detected. Create a .env file in the same folder as this, and put in it api-token = 'insert token here'. You get your token from https://platform.openai.com/")
    exit()
check_for_new_books()
load_embedding()
while True:
    user_question = input("Ask Question: ")
    gtp_main(user_question)