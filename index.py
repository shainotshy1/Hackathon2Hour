from openai import OpenAI
import json
import PyPDF2
from flask import Flask

app = Flask(__name__)

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

def pdf_to_string(pdf_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            markdown_text = ""
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                markdown_text += f"## Page {page_number}\n\n{text}\n\n"
            return markdown_text
    except Exception as e:
        return f"An error occurred: {e}"

class Mix():
    def __init__(self, el1, el2, result, explanation, valid):
        self.el1, self.el2 = sorted([el1, el2])
        self.result = result
        self.explanation = explanation
        self.valid = valid

class Mixer():
    def __init__(self, text, starter_elements):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"You are helping me create a science game where the user puts together items to produce new items, for an educational purpose. \
                           You are provided a textbook and first must give me all the import items from the text, all of which are biological things. \
                           The output of this request must be in a comma separated list like such with as many items as possible: element1, element2, element3, ... \
                           Have no other text output except for the list and do not add any delimiters except for commas. Don't choose items that represent types of science fields, only the actual real life things. \
                           Make each item in the list as unique as possible from each other. The textbook input is the following: {text}",
                }
            ],
            model="nvidia/llama-3.1-nemotron-70b-instruct",
        )
        response = chat_completion.choices[0].message.content
        self.base_elements = [item.strip() for item in response.split(",")]

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"You are a science expert. I will give you a list of biological things. I want to be able to use only {starter_elements} items from this list to discover the rest of the list of items. I will \
                                 do this by combining items in the list with eachother where these combinations yield other terms in the list. Give me the {starter_elements} most likely base key terms that \
                                 generate the rest of the terms. These terms must be the smallest possible things that must not be subsets of each other, biologically speaking. The output of this request must be in a comma separated list like such: element1, element2, element3, element4 \
                                 Have no other text output except for the list and do not add any delimiters except for commas. \
                                 Here are the biological things: {response}",
                }
            ],
            model="nvidia/llama-3.1-nemotron-70b-instruct",
        )
        response = chat_completion.choices[0].message.content
        self.discovered = set([item.strip() for item in response.split(",")])
        print(self.discovered)
        print(sorted(self.base_elements))
        self.d = {}

    def combine_elements(self, el1, el2):
        elements_in = tuple(sorted([el1, el2]))
        
        if elements_in in self.d:
            return self.d[elements_in]
        else:
            base_prompt = f"You are a science expert that is given two items and returns what is most likely created by combining those two things. The thing that \
                    is created should come from the following list of items: {self.base_elements}. If none of these elements can be reasonably created with the passed in items, \
                    then you decide what other possible item could be created as a result. If the combination of items makes no sense or if one item is a subset of the other, make the result be the word 'NONE' " + \
                    "The output of this request must be in the following format, with no other text output except for what is given here, and no delimiters outside the brackets: " + \
                    """{   \
                    "result":"_",\
                    "explanation":"_"\
                    }""" + "Make the result a one word response unless it is absolutely necessary that the result be multiple words."
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": base_prompt + f" What is the result of combining {el1} with {el2}",
                    }
                ],
                model="nvidia/llama-3.1-nemotron-70b-instruct",
            )

            response = chat_completion.choices[0].message.content
            data = json.loads(response)
            element = data['result']
            valid = True
            if element == "NONE":
                print("Invalid combination")
                valid = False
            elif element not in self.discovered:
                self.discovered.add(element)
            explanation = data['explanation']
            mix = Mix(el1, el2, element, explanation, valid)
            self.d[elements_in] = mix

        mix = self.d[elements_in]
        print(f"{mix.el1} + {mix.el2} = {mix.result}")
        print(f"Explanation: {mix.explanation}")


textbook = pdf_to_string("textbook.pdf")
starter_elements = 4
mixer = Mixer(textbook, starter_elements)
mixer.combine_elements("phosphate group", "amino group")
