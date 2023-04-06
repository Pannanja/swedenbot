import json
import openai
from scripts import misc

MAX_TOKENS = 4096

#Compares the search term to all embeds in a list, and retruns the embedded data sorted

def find_relevant_embeds(search_term: str, openai_properties: dict, embed_data: list):
    user_question_vector = misc.get_embedding(search_term, openai_properties["embed_model"])
    embed_similarity = misc.vector_similarity(user_question_vector, embed_data["embeds"])
    embeds_chunk_tuples = list(zip(embed_data["chunks"],embed_similarity, embed_data["ref"]))
    sorted_results = sorted(embeds_chunk_tuples, key=lambda x: x[1], reverse=True)
    return sorted_results

#Formats references and appends them to the end of a string (usually a system prompt). It also returns a truncated version, to save space.

def append_embeds(sorted_embeds: list, system_prompt: str, openai_properties: dict):
    total_tokens = misc.token_count(system_prompt)
    prompts = 0
    while total_tokens < openai_properties["max_tokens_in_system_prompt"]:
        tokens_in_next_prompt = misc.token_count(sorted_embeds[prompts][0])
        total_tokens += tokens_in_next_prompt
        if total_tokens < openai_properties["max_tokens_in_system_prompt"]:
            prompts +=1
    relevant_content = [t[0] for t in sorted_embeds[:prompts]]
    relevant_ref = [t[2] for t in sorted_embeds[:prompts]]

    relevant_results_string = ''
    relevant_results_string_trunc = ''

    for i in range(len(relevant_content)):
        reference = f"{relevant_ref[i][0]} {relevant_ref[i][1]}[{relevant_ref[i][2]}]"
        relevant_results_string += f"{reference}: {relevant_content[i]} + '\n\n'"
        #trunc_content = relevant_content[i][:150].replace('\n', " ").strip()
        relevant_results_string_trunc += f"{reference}\n"

    system_prompt_with_embeds = system_prompt + relevant_results_string
    return system_prompt_with_embeds, relevant_results_string_trunc



def chat_gpt(system_prompt: str, user_input: str, properties: dict, prev_message_history: list):
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
        model=properties["token_model"],
        messages=message_history,
        temperature=properties["temperature"],
        stream=properties["streaming"],
        #max_tokens=tokens_left-20, #Maybe the token count gives an estimate? -20 fixes errors.
    )
    if properties["streaming"]:
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