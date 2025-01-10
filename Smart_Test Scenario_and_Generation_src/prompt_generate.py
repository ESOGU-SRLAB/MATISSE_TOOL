""" This module contains functions to generate prompts based on selected test elements like instructions and scoring elements. """

def generate_prompt(process_title, document_type, test_prompt, document_content, selected_test_name, selected_instruction_elements, test_instruction_elements, selected_scoring_elements, test_scoring_elements):
    """
    Generate a comprehensive prompt based on the selected test name, instruction elements, and scoring elements.
    """
    # # Testing Area
    # print(50*"-")
    # print("Selected Instruction Elements: ", selected_instruction_elements)
    # print(50*"-")
    # print("Test Instruction Elements: ", test_instruction_elements)
    # print(50*"-")
    # print("Selected Scoring Elements: ", selected_scoring_elements)
    # print(50*"-")
    # print("Test Scoring Elements: ", test_scoring_elements)
    # print(50*"-")


    # Initialize the list to store selected elements
    selected_elements = []

    # Combine Instruction Elements
    if selected_instruction_elements:
        for name, selected in selected_instruction_elements.items():
            if selected:
                content = "Instruction and consistency situation: \n" + test_instruction_elements.get(name, "")
                selected_elements.append(content)

    # Ensure test_scoring_elements is a dictionary before using .get()
    if isinstance(test_scoring_elements, dict):
        # Combine Scoring Elements
        if selected_scoring_elements:
            for name, selected in selected_scoring_elements.items():
                if selected:
                    content = "Scoring situation: \n " + test_scoring_elements.get(name, "")
                    selected_elements.append(content)
    # else:
    #     # Log or handle the error if test_scoring_elements is not a dictionary
    #     content = "Scoring situation: No scoring elements found due to improper format."
    #     selected_elements.append(content)

    # Create the Prompt
    combined_prompt = "\n\n".join(selected_elements)

    # JSON structure and explanations
    json_structure = f"""
    JSON Output Structure:

    {{
        "TestScenarios": [
            {{
                "ScenarioID": "{process_title}_Test_Scenario_1",
                "Title": "<Scenario Title>",
                "Description": "<Detailed scenario description at least 3 sentences. This is the most important part of the generate test scenario!>",
                "Objective": "<Objective or goal of the scenario>",
                "Category": "{selected_test_name}",
                "Comments": "<Any inconsistency or additional notes>"
            }}
        ]
    }}

    Guidelines for JSON Structure:
    - Ensure the ScenarioID is dynamic and matches the required format.

    Example JSON output:
    {{
        "ScenarioID": "Process_A_ModelX_Test_Scenario_1",
        "Title": "Verify Login Functionality",
        "Description": "Test the login functionality to ensure that users can successfully log in with valid credentials and are rejected with incorrect credentials. Additionally, verify that the system displays appropriate error messages for failed login attempts to guide users in correcting their input. Furthermore, ensure that the login session is maintained correctly, allowing users to access their accounts seamlessly after a successful login.",
        "Objective": "Validate user authentication mechanism.",
        "Category": "Functional Tests",
        "Comments": ""
    }}

    This document is classified as a {document_type}. When generating test scenarios, ensure that the structure, format, and content align with the nature of this document type.

    Document Content: 
    {document_content}
    """

    # Add JSON structure to the generated prompt
    full_prompt = f"{test_prompt}\n\n{combined_prompt}\n\n{json_structure}"
    return full_prompt
