import json
import openai
from scripts.config import config
from scripts import misc
import sys

MAX_TOKENS = 4096

def chat_gpt(system_prompt: str, user_input: str, prev_message_history: list):
    token_model = config.get('openai_properties','token_model')
    temperature = config.getfloat('openai_properties','temperature')
    stream = config.getboolean('openai_properties','streaming')
    if prev_message_history == None:
        message_history = [{"role":"system", "content": system_prompt}]
        message_history.append({"role":"user", "content": user_input})
        #tokens_left = MAX_TOKENS - misc.token_count(system_prompt)
    else:
        message_history = prev_message_history
        #message_history[0] = [{"role":"system", "content": system_prompt}]
        #tokens_left = MAX_TOKENS
        #for i, item in enumerate(prev_message_history):
            #tokens_left -= misc.token_count(prev_message_history[i]["content"])
    chatGPT = openai.ChatCompletion.create(
        model=token_model,
        messages=message_history,
        temperature=temperature,
        stream=stream,
        #max_tokens=tokens_left-20, #Maybe the token count gives an estimate? -20 fixes errors.
    )
    if stream:
        gpt_reply = ""
        for message in chatGPT:
            json_response = json.loads(str(message))
            try:
                word = json_response['choices'][0]['delta']['content']
                gpt_reply += word
                print(word, end="", flush=True)
            except Exception as e:
                pass
        print("")
    else:
        gpt_reply = chatGPT.choices[0].message.content
        print(gpt_reply)
    message_history.append({"role":"assistant", "content": gpt_reply})
    return(gpt_reply, message_history)