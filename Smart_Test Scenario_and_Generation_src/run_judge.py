""" This module is used to run the judge on the prompt and uploaded file. """

from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout
import json
import logging

# Run the judge on the prompt and uploaded file
def run_judge_on_prompt(judge_combined_prompt, uploaded_file):
    # Create the prompt
    prompt = f"""
    Evaluate the content of the relevant test scenario to ensure it aligns with the uploaded file provided in the prompt. You must evaluate the each requirement and then add the json structure to a file.

    JSON Output Structure:

    {{
        "Controls": [
            {{
                "ControlID": "<Given Control ID from 1 to n>",
                "Title": "<Give a title for the control according to the evaluation>",
                "Evaluation": "<Evaluation must be boolean. If the test scenario meets the relevant requirement, set it to True; otherwise, set it to False.>",
                "Comments": "<Any inconsistency or additional notes>"
            }}
            # Add more control for each requirement
        ]
    }}

    Document Content:
    {uploaded_file}

    {judge_combined_prompt}
    """
    # # Control data
    # print(prompt)
    # print(50*"-")

    # Run the judge with the prompt and uploaded file content to get the control data using llama3.2 model
    llm = Ollama(model="llama3.2", request_timeout=300.0, json_mode=True)
    resp = llm.complete(prompt)
    control_data = json.loads(resp.text)

    # Return the control data
    if control_data:
        # # Control data
        # print(control_data)
        return control_data
    else:
        return "Error: No valid response received."
