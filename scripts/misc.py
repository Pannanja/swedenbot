import tiktoken
import openai
import numpy


TOKEN_MODEL = "gpt-3.5-turbo"

#Gets the embedding value of a piece of text

def get_embedding(text: str, embed_model: str):
    embedding = openai.Embedding.create(
        input=text,
        model=embed_model,
    )
    return embedding["data"][0]["embedding"]

#Counts tokens in input

def token_count(text: str):
    encoding_model = tiktoken.encoding_for_model(TOKEN_MODEL)
    return len(encoding_model.encode(text))

#Checks how similar two vectors are, spits out a number between 0 and 1

def vector_similarity(question, vectors):
    vector_similarity_list = []
    for item in vectors:
        result = numpy.dot(numpy.array(question),numpy.array(item))
        vector_similarity_list.append(result)
    return vector_similarity_list
