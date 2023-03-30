import openai
import json
from scripts import misc

SUMMARIZE_TOKENS = 4096*.8
TOKEN_MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.8

#Doesn't work yet!

def summarize_chunks(chunk_list, reference_list):

    tokens_used = 0
    to_summarize = ""
    summary_list = []
    temp = 0

    current_chunk = 0

    current_section = reference_list[current_chunk][1]
    next_chunk_section = current_section
    

    while current_section == next_chunk_section and current_chunk < len(chunk_list):
        tokens_used += misc.token_count(chunk_list[current_chunk])
        current_chunk += 1
        next_chunk_section = reference_list[current_chunk][1]




    for i, item in enumerate(chunk_list):
        tokens_in_next_prompt = misc.token_count(item)
        if tokens_used + tokens_in_next_prompt > SUMMARIZE_TOKENS:
            tokens_in_next_prompt = 0
            print(f"-----------------To summarize:----------")
            print(to_summarize)
            summary = summarize_bot(to_summarize)
            summary_list.append(summary)
            to_summarize = ""
            tokens_used = 0
            #debug
            temp += 1
            if temp > 4:
                exit()
        else:
            tokens_used += tokens_in_next_prompt
            to_summarize += f"\n\n{item}"

def summarize_bot(text):
    message_history = []
    message_history.append({"role":"system", "content": "You are 'Swedenborg Summarize Bot'. You summarize text from Swedenborg's books in one paragraph written from the authors (Swedenborg) perspective."})
    message_history.append({"role":"user", "content": text})
    chatGPT = openai.ChatCompletion.create(
        model=TOKEN_MODEL,
        messages=message_history,
        temperature=TEMPERATURE,
        stream=True
    )
    gpt_reply = ""
    print("-------------Summary:----------------------")

    #Streams the response, so you can see it as it comes in.

    for message in chatGPT:
        json_response = json.loads(str(message))
        try:
            word = json_response['choices'][0]['delta']['content']
            gpt_reply += word
            print(word, end="", flush=True)
        except Exception as e:
            pass
    
    print("")
    return gpt_reply
