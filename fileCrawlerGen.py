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

def updateFile(data):
    with open("outputMCQ.md",'a') as f:
        f.write(data.strip()+"\n---\n")
def processData(data):
    systemPrompt ="""Develop a comprehensive set of 5 higher-order multiple-choice questions (MCQs) based on an attached document, adhering to Bloom's Taxonomy levels of Evaluate, Analyze, and Apply. Evaluate user answers after submission. Start by thoroughly analyzing the document line-by-line to comprehend every nuance before crafting your MCQs. The goal is to test deep conceptual understanding through practical or real-world related questions. ### Task Requirements 1. **Thorough Analysis**: Carefully read the attached document, analyzing specific lines and concepts. 2. **MCQ Creation **: - Focus on three cognitive domains: Evaluate, Analyze, and Apply. - Ensure each MCQ tests depth of understanding. - Incorporate real-world case studies or practical situations directly relevant to the document. - Questions should be challenging, enforcing a thoughtful distinction between answer options. - Include answer choices that are close in meaning to test thorough comprehension. 3. **Question Design**: - Ensure diversity in question content; each MCQ must be unique. - Reference the exact line(s) used as the basis for the question. - Questions should be understandable without requiring additional external information. - Be mindful of user experience - questions should be answerable within a reasonable time frame. ### Answer Key and User Interaction 1. Do **not** provide the answer key within the initial set of questions. 2. Instruct the user to submit answers in the format: "Question Number - Answer Option" (e.g., "1 - B"). 3. Evaluate the user’s submission after they respond. ### Post-Submission Feedback 1. **Evaluation**: - Mark each response as correct or incorrect. - Display only the incorrect answers in the feedback. - Calculate and present the percentage of correct responses. 2. **Feedback on Incorrect Answers**: - Clarify why the user’s chosen answer is incorrect. - Provide the correct answer with a reference to the appropriate line(s) from the document. - Aim for insightful, educational feedback to strengthen understanding. ### Formatting Guidelines - **Question Presentation**: - Number each question clearly. - After each question, provide a reference to the line(s) in the document that inspired the question. - List answer options clearly with letters "A, B, C, D," etc. - **Feedback Presentation**: - After evaluating user responses, clearly separate each section to enhance readability. # Steps 1. Thoroughly analyze the entire attached document. 2. Develop a total of 5 MCQs based on key ideas, engaging higher-order thinking (Evaluate/Analyze/Apply). 3. After each question, include the specific line(s) on which the MCQ reference is made. 4. Number the questions and use clear, similar answer options to prompt careful consideration. 5. After user submission: evaluate, mark responses, identify incorrect answers, offer detailed explanations, and provide a final score. # Output Format - **MCQs Presentation**: Present the MCQs in a numbered list, including: - **Question text**. - **Reference line(s)** from the document, right after the question. - **Answer options** labeled A, B, C, D. - **Evaluation Feedback** (after user submission): - **Correct/Incorrect** marking for each response. - If incorrect, provide: - A clear explanation of why the chosen option was wrong. - A reference to the specific part of the document supporting the correct answer. - **Percentage score** at the end. # Notes - Do not include any answer key with the initial question list. - Questions should be self-contained and not require any references to materials beyond what's attached. - Emphasize clarity and relevance to the document's content. - Remember, the ultimate goal is to foster deep learning and critical thinking in users. - Include a proper reference using the page number and the file name provided in the following format [ [<fileName>](./full_pdf_dataset/<fileName>), PageNumber:<pageNumber>]. - Just reply with the mcq nothing else avoid adding heading or footer. - Make sure the output is in markdown format with options in a standarize format."""
    session = [
           {"role": "system", "content":systemPrompt},
           {"role": "user", "content": data},
        ]
    result = generate_openai_completion(session)
    updateFile(result)
    print("Inserted")
def pdfToMcq(file_path):
    text =[]
    fileName = os.path.basename(file_path)
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            if len(page.extract_text())<=500:
                print(f"skipping the file {fileName}, page: {page.page_number}")
                continue

            text.append({"fileName":fileName, "pageNumber":page.page_number, "content":page.extract_text()})
            if page.page_number % TOTALPAGE ==0:
                print("1")
                try:
                    processData(json.dumps(text))
                except Exception as e:
                    return False
                print(f"file {fileName} Page number: {page.page_number} --done")
            else:
                print("0")
    return True

def main():
    files = os.listdir("full_pdf_dataset")
    for file in files[:2]:
        pdfToMcq(os.path.join("full_pdf_dataset", file))
        

if __name__=="__main__":
    main()


