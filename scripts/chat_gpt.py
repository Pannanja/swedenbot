import json
import openai
from scripts.config import config
from scripts import misc

def ask_question(user_question, save_data_cache, system_prompts, socketio=None):
    query_rewrite = config.getboolean('chatbot','query_rewrite')
    if query_rewrite:
        embed_search_terms = chat_gpt(system_prompts["query_rewrite"], user_question, None, None)[0]
    else:
        embed_search_terms = user_question
    sorted_embeds = misc.find_relevant_embeds(embed_search_terms, save_data_cache)
    system_prompt_with_embeds, relevant_results = misc.append_embeds(sorted_embeds, system_prompts["swedenbot"])
    gtp_reply = chat_gpt(system_prompt_with_embeds, user_question, None, socketio)[0]
    if socketio != None:
        socketio.emit("gpt_response", {"word": "|||", "sources": relevant_results})
    print(relevant_results)
    return(gtp_reply, relevant_results)


def chat_gpt(system_prompt: str, user_input: str, prev_message_history: list, socketio):
    token_model = config.get('openai_properties','token_model')
    temperature = config.getfloat('openai_properties','temperature')
    stream = config.getboolean('openai_properties','streaming')
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
                else:
                    print(word, end="", flush=True)
                gpt_reply += word
            except Exception as e:
                pass
        print("")
    else:
        gpt_reply = chatGPT.choices[0].message.content
        if socketio != None:
            socketio.emit("gpt_response", {"word": gpt_reply})
        print(gpt_reply)
    message_history.append({"role":"assistant", "content": gpt_reply})
    return(gpt_reply, message_history)