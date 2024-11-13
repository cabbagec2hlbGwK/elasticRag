import elasticsearch
import pdfplumber
import json
import os
from openai import OpenAI


openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)
TOTALPAGE=3

def generate_openai_completion(message):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=message
    )
    return response.choices[0].message.content

def updateFile(data, fileName):
    with open(os.path.join("output",fileName.replace(".pdf",".md")),'w') as f:
        f.write(data.strip())
def processData(data):
    systemPrompt ="""As an AI language model specializing in educational content creation, your task is to develop a set of critical multiple-choice questions (MCQs) based on an attached document. Please adhere strictly to the following instructions: Thorough Analysis of the Document: Thoroughly read and analyze the attached document. Go through each line to fully comprehend its meaning and nuances. Creation of Critical MCQs: Create a total of 5 MCQs. Focus on higher-order thinking skills according to Bloom's Taxonomy, specifically the levels of Evaluate, Analyze, and Apply. Ensure each question assesses the user's deep understanding of the content. Incorporate real-world applications or case studies related to the document's content to enhance relevance and practical understanding. Question Design: Craft questions that are challenging and thought-provoking. Include at least two answer options that are very similar to each other, requiring careful consideration to choose the correct one. Ensure that only someone who has thoroughly understood the document can answer correctly. Each MCQ must be unique and not repetitive. Design questions to be answerable within a reasonable time frame to respect the user's time. For each MCQ, provide the exact line(s) from the document on which the question is based, highlighting the critical information used. Answer Key and User Interaction: Do not provide the answer key along with the questions. Present all the questions in one response. Instruct the user to provide their answers in the format: "Question Number - Answer Option" (e.g., "1 - B"). Evaluation of User Responses: Upon receiving the user's answers, evaluate each response. Mark each question as Correct or Incorrect. Only show the incorrect answers in your feedback. Calculate and provide the percentage of correct answers at the end of the evaluation. Feedback on Incorrect Answers: For each question answered incorrectly, provide a detailed explanation: Clarify why the chosen option is incorrect. Explain the correct answer with reference to the relevant parts of the document. Provide the exact reference to the code or specific line(s) from the document to enhance understanding. Aim to enhance the user's understanding of the material. Additional Guidelines: Use clear and professional language throughout. Maintain academic integrity by avoiding any form of bias or disallowed content. Ensure the questions are self-contained and understandable without requiring external information. Formatting: Number each question sequentially. After each question, include the exact line(s) from the document on which it is based, before listing the answer options. List the answer options as A, B, C, D, etc. After the user submits answers and you provide feedback, clearly separate each section for readability."""
    session = [
           {"role": "system", "content":systemPrompt},
           {"role": "user", "content": data},
        ]
    result = generate_openai_completion(session)
    return result
    print("Inserted")
def pdfToMcq(file_path):
    text =[]
    fileName = os.path.basename(file_path)
    mcq = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            if len(page.extract_text())<=500:
                print(f"skipping the file {fileName}, page: {page.page_number}")
                continue

            text.append({"fileName":fileName, "pageNumber":page.page_number, "content":page.extract_text()})
            if page.page_number % TOTALPAGE ==0:
                print("1")
                try:
                    mcq += processData(json.dumps(text))+"\n --- \n"
                except Exception as e:
                    return False
                print(f"file {fileName} Page number: {page.page_number} --done")
            else:
                print("0")
    updateFile(mcq, fileName)
    return True

def main():
    files = os.listdir("full_pdf_dataset")
    for file in files[:2]:
        pdfToMcq(os.path.join("full_pdf_dataset", file))
        

if __name__=="__main__":
    main()


