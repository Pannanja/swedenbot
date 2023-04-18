import json
import openai
from scripts.config import config
from scripts import misc
from typing import Dict, Tuple
from scripts import embed


def import_system_prompts(prompt_file: str) -> Dict[str,str]:
    """
    Loads the system prompts used by ChatGTP from a text file

    Arg: The file name and directory that contains the prompts

    Returns: The system prompts as a dict, with the key being the name of the prompt and the value being the prompt.
    """
    system_prompts = {}
    with open(prompt_file, "r") as prompts:
        for prompt in prompts:
            stripped_prompt = prompt.strip()
            if stripped_prompt != None:
                name, text = stripped_prompt.split(' = ')
                system_prompts[name] = text
    return system_prompts

def ask_swedenbot(user_question: str, save_data_cache: dict, temperature: float, socketio=None) -> Tuple[str, list]:
    """
    Runs a question through Swedenbot.

    Args:
        user_question: The user question
        save_data_cache: a dict with embeds
        temperature: The temperature (0-1) of ChatGPT (0 more literal, 1 more creative)
        socketio: An optional argument to define the socketio for Flask
    """
    query_rewrite = config.getboolean('chatbot','query_rewrite')
    if query_rewrite:
        embed_search_terms = chat_gpt(system_prompts["query_rewrite"], user_question, None, None, 0.5)[0]
    else:
        embed_search_terms = user_question
    sorted_embeds = embed.find_relevant_embeddings(embed_search_terms, save_data_cache)
    system_prompt_with_embeds, relevant_results = append_embeds(sorted_embeds, system_prompts["swedenbot"])
    gtp_reply = chat_gpt(system_prompt_with_embeds, user_question, None, socketio, temperature)[0]
    if socketio != None:
        socketio.emit("gpt_response", {"word": "|||", "sources": relevant_results})
    return(gtp_reply, relevant_results)


def chat_gpt(system_prompt: str, user_input: str, prev_message_history: list, socketio, temperature):
    token_model = config.get('openai_properties','token_model')
    stream = config.getboolean('openai_properties','streaming')
    software_model = config.get('model','software_model')
    if prev_message_history == None:
        message_history = [{"role":"system", "content": system_prompt}]
        message_history.append({"role":"user", "content": user_input})
    else:
        message_history = prev_message_history
    chatGPT = openai.ChatCompletion.create(
        model=token_model,
        messages=message_history,
        temperature=temperature,
        stream=stream,
    )
    if stream:
        gpt_reply = ""
        for message in chatGPT:
            json_response = json.loads(str(message))
            try:
                word = json_response['choices'][0]['delta']['content']
                if socketio != None:
                    socketio.emit("gpt_response", {"word": word})
                elif software_model == "console":
                    print(word, end="", flush=True)
                gpt_reply += word
            except Exception as e:
                pass
        if software_model == "console":
            print("")
    else:
        gpt_reply = chatGPT.choices[0].message.content
        if socketio != None:
            socketio.emit("gpt_response", {"word": gpt_reply})
        elif software_model == "console":
            print(gpt_reply)
    message_history.append({"role":"assistant", "content": gpt_reply})
    return(gpt_reply, message_history)

system_prompts = import_system_prompts("prompts.txt")

#Formats references and appends them to the end of a string (usually a system prompt). It also returns a truncated version, to save space.

def append_embeds(sorted_embeds: list, system_prompt: str):
    max_tokens_in_system_prompt = config.getint('openai_properties','max_tokens_in_system_prompt')
    total_tokens = misc.count_tokens(system_prompt)
    prompts = 0
    while total_tokens < max_tokens_in_system_prompt:
        tokens_in_next_prompt = misc.count_tokens(sorted_embeds[prompts][0])
        total_tokens += tokens_in_next_prompt
        if total_tokens < max_tokens_in_system_prompt:
            prompts +=1
    relevant_content = [t[0] for t in sorted_embeds[:prompts]]
    relevant_ref = [t[2] for t in sorted_embeds[:prompts]]

    relevant_results_string = ''
    relevant_results_string_trunc = []
    source_character_limit = int(config.get('chatbot','source_character_limit'))

    for i in range(len(relevant_content)):
        reference = f"{relevant_ref[i][0]} {relevant_ref[i][1]}[{relevant_ref[i][2]}]"
        relevant_results_string += f"{reference}: {relevant_content[i]} + '\n\n'"
        trunc_content = relevant_content[i][:source_character_limit].replace('\n', " ").strip()
        relevant_results_string_trunc.append(f"{reference}\n{trunc_content}...")

    system_prompt_with_embeds = system_prompt + relevant_results_string
    return system_prompt_with_embeds, relevant_results_string_trunc
