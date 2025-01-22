""" This module contains the function to generate test cases based on the generated test scenario. """

from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout
import json

# Function to generate a JSON structure for test scenarios
def generate_json_structure():
    """
    Generates a JSON structure for test scenarios with a dynamic Test Case ID after ScenarioID.

    Returns:
        str: A formatted JSON structure as a string.
    """
    json_structure = """
    JSON Output Structure:

    {
        "TestCases": [
            {
                "ScenarioID": "<Dynamic Scenario ID>",
                "TestCaseID": "<Dynamic Test Case ID>",
                "Title": "<Scenario Title>",
                "Description": "<Detailed scenario description at least 3 sentences. This is the most important part of the test scenario!>",
                "Objective": "<Objective or goal of the scenario>",
                "Category": "<Category of the test case>",
                "Comments": "<Any inconsistency or additional notes>"
            }
        ]
    }

    Guidelines for JSON Structure:
    - Ensure the ScenarioID is dynamic and matches the required format.
    - TestCaseID must be unique within the scope of its ScenarioID.

    Example JSON output:
    {
        "ScenarioID": "Scenario_1",
        "TestCaseID": "TestCase_1",
        "Title": "Verify Login Functionality",
        "Description": "Test the login functionality to ensure users can log in with valid credentials and receive appropriate error messages for invalid inputs. Additionally, ensure session management operates correctly post-login.",
        "Objective": "Validate user authentication mechanism.",
        "Category": "Functional Tests",
        "Comments": "Ensure edge cases for invalid inputs are covered."
    }
    """
    # Return the JSON structure as a string
    return json_structure

# Function to generate test cases based on the generated test scenario
def generate_test_case(model, combined_prompt, max_retries=3):
    """
    Generates test cases based on the generated test scenario.
    """

    # Initialize the number of attempts
    attempts = 0
    required_keys = {
        "ScenarioID",
        "TestCaseID",
        "Title",
        "Description",
        "Objective",
        "Category",
        "Comments",
    }
    
    # Try to generate test cases using the LLM model
    while attempts < max_retries:
        # Attempt to connect to the LLM model and generate test cases
        try:
            # Initialize the LLM model
            llm = Ollama(model=model, request_timeout=300.0, json_mode=True)
            resp = llm.complete(combined_prompt) # Generate test cases
            
            # Parse the JSON text into a Python dictionary
            try:
                test_case_llm_output_json = json.loads(resp.text)  # JSON string to dict
            except json.JSONDecodeError as decode_error:
                raise ValueError(f"Failed to parse JSON from LLM response: {decode_error}")
            # Return the validated JSON output
            return test_case_llm_output_json
        
        except (json.JSONDecodeError, KeyError) as e:
            # JSON parsing error or missing key
            attempts += 1
            if attempts >= max_retries:
                raise ValueError(f"Error: All attempts failed. Last error: {e}")
        except (ConnectionError, Timeout) as e:
            # Connection or timeout error
            attempts += 1
            if attempts >= max_retries:
                raise ConnectionError(f"Error: All attempts failed due to connection issues. Last error: {e}")
        except Exception as e:
            # Any other unexpected error
            attempts += 1
            if attempts >= max_retries:
                raise RuntimeError(f"Error: All attempts failed due to an unexpected error. Last error: {e}")
