""" This script is used to run the model on the prompt and save the output to the database. """

from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout
import json
import logging

# Validation of JSON structure (expected format) with the required keys
def validate_json_structure(data):
    """ Validates that the JSON structure matches the expected format defined by Formal-LLM."""
    required_keys = {"TestScenarios"}
    if isinstance(data, dict) and required_keys.issubset(data.keys()):
        for scenario in data["TestScenarios"]:
            if not all(key in scenario for key in [
                "ScenarioID", "Title", "Description", 
                "Objective", "Category", "Comments"
            ]):
                return False
        return True
    return False

# Run the model on the prompt and return the test scenarios. If it does not be successful, retry up to 3 times.
def run_model_on_prompt(model, prompt, max_retries=3):
    # Initialize retry count
    attempts = 0

    # Retry up to 3 times
    while attempts < max_retries:
        try:
            # Run the model on the prompt to generate test scenarios
            llm = Ollama(model=model, request_timeout=300.0, json_mode=True)
            resp = llm.complete(prompt)

            # Log the raw response for debugging purposes
            logging.info(f"Attempt {attempts + 1}: Raw response received: {resp.text}")

            # Parse the JSON text into a Python dictionary
            test_scenarios_dict = parse_json_response(resp.text)

            if test_scenarios_dict:
                # Save the JSON file if parsing was successful
                return test_scenarios_dict
            else:
                logging.warning("Parsed JSON does not match the expected structure. Retrying...")

        except (ConnectionError, Timeout) as e:
            logging.error(f"Connection error or timeout occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

        # Increment the retry count
        attempts += 1

    # If all attempts fail, log and print an error message
    logging.error("All attempts to parse the JSON response failed after 3 tries.")

    # Control the JSON structure
    print("Error: All attempts to parse the JSON response failed after 3 tries.")

# Parse the JSON response, ensuring it matches the expected format. Returns the dictionary if successful, None otherwise.
def parse_json_response(json_text):
    """
    Parses the JSON response, ensuring it matches the expected format.
    Returns the dictionary if successful, None otherwise.
    """
    try:
        # Clean the JSON text by removing newlines and escape characters
        json_text = json_text.replace('\n', '').replace('\\n', '').replace('\\"', '"')

        # Load the JSON text into a Python dictionary
        parsed_data = json.loads(json_text)

        # Control the JSON structure
        if validate_json_structure(parsed_data):
            return parsed_data
        else:
            logging.warning("Parsed JSON does not match the expected structure.")
            return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding failed: {e}")
        return None

# Save the model output to the database using the session ID
def validate_json_structure(data):
    """
    Validates that the JSON structure matches the expected format defined by Formal-LLM.
    This ensures the response aligns with the constraints and requirements.
    """
    required_keys = {"TestScenarios"}
    if isinstance(data, dict) and required_keys.issubset(data.keys()):
        # Additional checks for the structure of each scenario can be implemented here
        for scenario in data["TestScenarios"]:
            if not all(key in scenario for key in ["ScenarioID", "Title", "Description", "Objective", "Category", "Comments"]):
                return False
        return True
    return False


# Save the model output to the database using the session ID
# If each session is running independently and one session is not switched to the next before it is completed, 
# there is no risk of data being mixed up. Therefore, the existing save_model_output_to_db function will be sufficient.
def save_model_output_to_db(session_id, model_output, db):
    """
    Saves the model output to the 'sessions' collection under the specified session ID.
    """
    collection = db["sessions"]
    collection.update_one(
        {"session_id": session_id},  # Match the document with the session_id
        {"$set": {"model_output": model_output}},  # Update or insert 'model_output' at the root level
        upsert=True  # Create the document if it doesn't exist
    )

