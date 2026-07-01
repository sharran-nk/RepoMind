import ollama


MAX_CHARS = 6000


def generate_embedding(text):


    if len(text) > MAX_CHARS:

        text = text[:MAX_CHARS]


    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )


    return response["embedding"]