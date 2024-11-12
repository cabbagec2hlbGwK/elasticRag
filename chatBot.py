## Install the required packages
## pip install -qU elasticsearch openai
import os
import re
from rich.console import Console
from rich.markdown import Markdown
from elasticsearch import Elasticsearch
from openai import OpenAI


console = Console()
es_client = Elasticsearch(
    "https://071730c04c944f729330b0129af38419.us-central1.gcp.cloud.es.io:443",
    api_key=os.environ["elasticcloud"]
)
      
openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)
index_source_fields = {
    "dc-ecinf-index": [
        "text"
    ]
}
def get_elasticsearch_results(query):
    es_query = {
        "retriever": {
            "standard": {
                "query": {
                    "nested": {
                        "path": "text.inference.chunks",
                        "query": {
                            "sparse_vector": {
                                "inference_id": "dc-ec-inf",
                                "field": "text.inference.chunks.embeddings",
                                "query": query
                            }
                        },
                        "inner_hits": {
                            "size": 2,
                            "name": "dc-ecinf-index.text",
                            "_source": [
                                "text.inference.chunks.text"
                            ]
                        }
                    }
                }
            }
        },
        "size": 3
    }
    result = es_client.search(index="dc-ecinf-index", body=es_query)
    return result["hits"]["hits"]


def extractFilenamePage(text):
    # Regex patterns to extract the fileName and pageNumber
    filename_pattern = r'"fileName":\s*"([^"]+)"'
    page_number_pattern = r'"pageNumber":\s*(\d+)'
    
    # Using re.search to find the matches based on the above patterns
    filename_match = re.search(filename_pattern, text)
    page_number_match = re.search(page_number_pattern, text) 
    
    # Extracting the matched filename and page_number
    filename = filename_match.group(1) if filename_match else None
    page_number = int(page_number_match.group(1)) if page_number_match else None
    
    return filename, page_number

def getContext(results):
    context = ""
    for hit in results:
        fileName, pageNumber = extractFilenamePage(str(hit))
        pageNumber = int(pageNumber)-1
        inner_hit_path = f"{hit['_index']}.{index_source_fields.get(hit['_index'])[0]}"
        ## For semantic_text matches, we need to extract the text from the inner_hits
        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            context += f'\n FILE_NAME:{fileName}, PAGE_NUMBER:{pageNumber}\n --- \n'.join(inner_hit['_source']['text'] for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits'])
        else:
            source_field = index_source_fields.get(hit["_index"])[0]
            hit_context = hit["_source"][source_field]
            context += f"{hit_context}\n FILE_NAME:'{fileName}' PAGE_NUMBER:'{pageNumber}' \n\n ---"
    return str(context)

def create_openai_prompt(question, results):
    context = ""
    for hit in results:
        fileName, pageNumber = extractFilenamePage(str(hit))
        pageNumber = int(pageNumber)-1
        inner_hit_path = f"{hit['_index']}.{index_source_fields.get(hit['_index'])[0]}"
        ## For semantic_text matches, we need to extract the text from the inner_hits
        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            context += f'\n FILE_NAME:{fileName}, PAGE_NUMBER:{pageNumber}\n --- \n'.join(inner_hit['_source']['text'] for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits'])
        else:
            source_field = index_source_fields.get(hit["_index"])[0]
            hit_context = hit["_source"][source_field]
            context += f"{hit_context}\n FILE_NAME:'{fileName}' PAGE_NUMBER:'{pageNumber}' \n\n ---"
    prompt = f"""
  UserQuestion:{{{question}}}
  Context:{{{context}}}
  """
    return prompt
def generate_openai_completion(message):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=message
    )
    return response.choices[0].message.content

def main():
    systemPrompt = """
      Instructions:
      
      - You are an assistant for question-answering tasks.
      - Answer questions truthfully and factually using only the context and older conversation provided.
      - If you don't know the answer and the answer is not in the context, just reply as Null, don't make up an answer.
      - You must always cite the document where the answer was extracted using inline academic citation style [], using the position.
      - Use markdown format for code examples.
      - You are correct, factual, precise, and reliable.
      - the context will have the FILE_NAME and the PAGE_NUMBER use that to cite the answer.
      - If the context dose not have the answer just reply as Null.
      - User can ask questions about previous message so understand the request and read all the message from the role assistant and user

      Steps:
          1. Understand the conversation between user and assistant.
          2. If ther is no information avaliable in the given conversation then check the context provided in the corrent question for answers.
          3. If ther is no related information avaliable in prevous messages and replies or the context reply as Null
          4. If ther is information. understand the provided data and reply the user question
      
      ## Example:
      UserQuestion:{userQuestion}
      Context:{context}\n\n"""
    additionInstruction = """
    Instruction:
        - Answer this question based on the previous conversation if ther is no information matching the question in the replies reply saying just Null.
        - Try to answer if the information is alredy avaliable in the previous conversation.
        - If the question needs more information to answer saying INFO{'And provide all the keywords related the question to extract more information on the topic here'}.
        - If ther is no context avaliable or need more information to make decision reply with the INFO{'with all the keywords avaliable from the information present '}.
    """
    session = [
            {"role": "system", "content":systemPrompt},
           # {"role": "user", "content": question},
        ]
    while True:
        contextLength = len(str(session))
        print("-"*100)
        print(f"Current context length {contextLength}")
        if contextLength >= 30000:
            print("Context Overflow.....")
            session = [
                    {"role": "system", "content":systemPrompt},
                   # {"role": "user", "content": question},
                ]
            print("Context has been reset")
        question = input("*>> Enter the question: ")
        contextPrompt = create_openai_prompt(question, "")
        index = len(session)
        contextPrompt+= additionInstruction
        session.append({"role": "user", "content": contextPrompt})
        result = generate_openai_completion(session)
        contextGlobal = ""
        if "INFO" in result:
            print(f"Featching context for {result}")
            context = get_elasticsearch_results(question+result.replace("INFO",""))
            session.pop()
            contextPrompt = create_openai_prompt(question, context)
            session.append({"role": "user", "content": contextPrompt})
            result = generate_openai_completion(session)
            contextGlobal = context
        if "Null" in result:
            print(f"New context injected--")
            context = get_elasticsearch_results(question)
            session.pop()
            contextPrompt = create_openai_prompt(question, context)
            session.append({"role": "user", "content": contextPrompt})
            result = generate_openai_completion(session)
            contextGlobal = context
        session.append({"role": "assistant", "content": str(result)})
        session[index]["content"] = str(session[index]["content"]).replace(getContext(contextGlobal),"")
        fmtData = Markdown(result)
        console.print(fmtData)



if __name__ == "__main__":
    main()
