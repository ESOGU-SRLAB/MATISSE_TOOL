""" This module contains functions to validate the inputs for the prompt generation process. It checks if all required fields are provided. """

# Validate if all required inputs for combined_prompt are provided
def validate_combined_prompt(
    process_title, 
    document_type, 
    test_prompt, 
    document_content,
    selected_test_name,
    selected_instruction_elements, 
    test_instruction_elements, 
    selected_scoring_elements, 
    test_scoring_elements
):
    """
    Validate if all required inputs for combined_prompt are provided.
    
    Args:
        process_title (str): Title of the process.
        document_type (str): Type of the document.
        test_prompt (str): Test prompt text.
        document_content (str): Content of the document.
        selected_test_name (str): Selected test name.
        selected_instruction_elements (dict): Selected instruction elements.
        test_instruction_elements (dict): Available instruction elements.
        selected_scoring_elements (dict): Selected scoring elements.
        test_scoring_elements (dict): Available scoring elements.

    Returns:
        tuple: (bool, list) True if all inputs are valid, False otherwise, and a list of missing elements.
    """
    missing_fields = []
    
    # Check if all required fields are provided
    if not process_title:
        missing_fields.append("process_title")
    if not document_type or document_type == "--Please Select a Type--":
        missing_fields.append("document_type")
    if not test_prompt:
        missing_fields.append("test_prompt")
    if not document_content:
        missing_fields.append("document_content")
    if not selected_test_name or selected_test_name == "--Please Select a Test Type--":
        missing_fields.append("selected_test_name")
    if not selected_instruction_elements or not any(selected_instruction_elements.values()):
        missing_fields.append("selected_instruction_elements")
    if not test_instruction_elements:
        missing_fields.append("test_instruction_elements")
    if not selected_scoring_elements or not any(selected_scoring_elements.values()):
        missing_fields.append("selected_scoring_elements")
    if not test_scoring_elements:
        missing_fields.append("test_scoring_elements")
    
    # Return True if all required fields are provided, False otherwise
    if missing_fields:
        return False, missing_fields
    return True, []