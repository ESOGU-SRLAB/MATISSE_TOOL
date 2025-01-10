""" This module generates a specialized test prompt based on the provided inputs, including a document's type, content, and a selected test name. The generated prompt is customized to align with the selected test name and the document's characteristics, ensuring precise and context-specific test scenario generation. The resulting prompt is designed to guide the creation of high-quality test scenarios that adhere to ISTQB standards and methodologies. The module utilizes the llama3.2 model through the Ollama. """

from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout
import json

# Function to create a specialized test prompt based on the provided inputs
def create_customise_test_prompt(selected_test_name, document_type, document_content, test_prompt):
    """
    This function generates a specialized test prompt based on the provided inputs, including a document's type, content, and a selected test name.
    The generated prompt is customized to align with the selected test name and the document's characteristics, ensuring precise and context-specific test scenario generation.
    The resulting prompt is designed to guide the creation of high-quality test scenarios that adhere to ISTQB standards and methodologies.
    """

    # Define the prompt template for the prompt generator
    prompt_generator_prompt = f"""
    You are a highly skilled prompt engineer tasked with creating a highly dynamic and adaptable test prompt. This test prompt must be customizable based on the given inputs, including a document’s type, content, and a specified test focus. Your goal is to generate a prompt that enables precise, ISTQB-compliant, and context-specific test scenario generation, strictly tailored to the provided document's characteristics and the selected test type. Just give a JSON format as a response.

    The resulting prompt must:
    1. Explicitly address the provided document type and its testing implications.
    2. Focus on the selected test name, ensuring alignment with its methodologies and standards.
    3. Avoid unnecessary generalizations or assumptions and rely solely on the document content and inputs for scenario creation.
    4. Produce a clear and structured testing prompt that can guide the generation of actionable and accurate test scenarios.
    5. Generally, provide a detailed and comprehensive outline for creating high-quality test scenarios based on the document's specifics.
    6. Maximum 2 paragraphs and 1000 words.
    7. Generated test scenario prompt must have a purpose of generating maximum test scenarios based on the document content and selected test name.
    8. Generated test scenario prompt must be in JSON format.
    9. Just give a JSON format as a response.


    Ensure the generated test prompt includes the following elements:
    - General purposes and objectives of the test, emphasizing the selected test name and its relevance to the document type and content.
    - A professional and authoritative tone, establishing the tester’s expertise.
    - Clear instructions that define the testing scope, objectives, and methods.
    - Steps that emphasize deriving test cases, input conditions, expected outputs, and error-handling mechanisms directly from the document content.
    - ISTQB alignment for accuracy, completeness, and robustness.

    The generated test prompt must dynamically adapt to the provided inputs and produce actionable and relevant instructions for creating high-quality test scenarios.

    Selected Test Name: {selected_test_name}
    Document Type: {document_type}
    Document Content: 
    {document_content}

    Based on the provided inputs, create a specialized test prompt that aligns with the selected test name and the document's type and content. Ensure the prompt is detailed, focused, and tailored to the specific testing requirements.

    IMPORTANT: You must generate a test prompt based on general test prompt and the provided document content. The test prompt should be customised to the selected test name, document type, and document content!

    General Test Prompt for {selected_test_name}: {test_prompt}

    Give the customised test prompt in JSON format.
    The JSON format should include the following fields:
    Example JSON output:
    {{
        custom_test_prompt: "Your generated test prompt here"
    }}

    Just give a JSON format as a response.
    """

    # Return the prompt template for the prompt generator
    return prompt_generator_prompt


# Function to generate a specialized test prompt based on the provided inputs
def generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt, max_retries=3):
    """
    This function generates a specialized test prompt based on the provided inputs, including a document's type, content, and a selected test name.
    The generated prompt is customized to align with the selected test name and the document's characteristics, ensuring precise and context-specific test scenario generation.
    The resulting prompt is designed to guide the creation of high-quality test scenarios that adhere to ISTQB standards and methodologies.
    The function handles potential connection errors and retries the request up to a maximum. Max retries can be adjusted as needed but the default is 3.
    """

    # Create a customised test prompt based on the provided inputs
    customised_prompt = create_customise_test_prompt(selected_test_name, document_type, document_content, test_prompt)
    # Initialize the number of attempts
    attempts = 0

    # Try to generate a specialized test prompt using the LLM model
    while attempts < max_retries:
        # Attempt to connect to the LLM model and generate a specialized test prompt
        try:
            llm = Ollama(model="llama3.2", request_timeout=300.0, json_mode=True) # Initialize the LLM model
            resp = llm.complete(customised_prompt) # Generate a specialized test prompt
            
            # Parse the JSON text into a Python dictionary
            generated_customise_prompt = json.loads(resp.text)  # JSON string to dict
            
            # Check if the parsed JSON contains the required key
            if "custom_test_prompt" in generated_customise_prompt:
                return generated_customise_prompt["custom_test_prompt"]
            else:
                raise KeyError("Expected 'custom_test_prompt' key not found in the response.")

        except (json.JSONDecodeError, KeyError) as e:
            # JSON parsing error or missing key
            attempts += 1
            # Retry if attempts are within the limit
            if attempts >= max_retries:
                raise ValueError(f"Error: All attempts failed. Last error: {e}")
        except (ConnectionError, Timeout) as e:
            # Connection or timeout error
            attempts += 1
            # Retry if attempts are within the limit
            if attempts >= max_retries:
                raise ConnectionError(f"Error: All attempts failed due to connection issues. Last error: {e}")
        except Exception as e:
            # Any other unexpected error
            attempts += 1
            # Retry if attempts are within the limit
            if attempts >= max_retries:
                raise RuntimeError(f"Error: All attempts failed due to an unexpected error. Last error: {e}")


# # Testing Area
# selected_test_name = "Functional Tests"
# document_type = "Requirement Document"
# document_content = """
# 1. Users should be able to create, edit, and delete tasks.
# 2. Users should organize tasks under specific projects or categories.
# 3. Users can mark tasks as completed, pending, or in progress.
# 4. Users can set due dates and receive reminders for tasks.
# 5. Users can filter and view tasks based on status (completed, pending, in-progress)."""
# test_prompt = "Acting as a senior ISTQB-certified test analyst, design a detailed functional test scenario focused on evaluating the system’s core functionalities against specified requirements. This scenario should assess whether the system performs its intended operations correctly, meeting both functional specifications and expected user behaviors. Clearly define the purpose of the test, including necessary preconditions, setup configurations, and initial data required. Identify the primary functions to be tested, including input conditions, expected outputs, and any error-handling mechanisms. Outline specific test steps that simulate realistic user actions to validate each function. Describe the expected outcomes for each step, ensuring that both positive and negative cases are covered. Emphasize that the scenario aligns with ISTQB functional testing standards, aiming for accuracy, completeness, and robustness in functional validation."

# # Example Usage
# print(generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt))
