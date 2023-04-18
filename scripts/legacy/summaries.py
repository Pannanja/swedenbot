from scripts import chat_gpt

OPENAI_PROPERTIES = {
    "token_model" : "gpt-3.5-turbo",
    "embed_model" : "text-embedding-ada-002",
    "temperature" : 0.8,
    "streaming" : True,
    "max_tokens_in_system_prompt" : 2700
}


#Doesn't do anything yet!

def summarize_chunks(chunk_list, reference_list):
    section_chunk_list = [""]
    section_reference_list = [""]
    last_reference = None
    for i in range(len(reference_list)):
        if last_reference == reference_list[i][1]:
            section_chunk_list[-1] += chunk_list[i]
        else:
            section_chunk_list.append(chunk_list[i])
            section_reference_list.append(reference_list[i])
            last_reference = reference_list[i][1]
    for i in range(10):
        print(section_reference_list[i])
        print(section_chunk_list[i])
    exit()