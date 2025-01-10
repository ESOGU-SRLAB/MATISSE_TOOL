""" 
This script is for analyzing a document content document to see if it is suitable for different types: 
Functional Tests, Performance Tests, Usability Tests, Security Tests, and Extensibility Tests. 
The script uses the llama3.2 model to analyze the document content and return the results as follows, 
with each test type containing a 'suitability' and 'explanation'. 
"""

from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout

# Analyze the document content to determine its suitability for different types of testing
# Input: document content (str)
# Output: analysis results (str)
def analyse_document(document):
    """ This function analyzes the document content to determine its suitability for different types"""

    # This prompt tells the LLM how to analyze the document and what kind of test results are needed.
    prompt = """
    Analyze the document to determine its suitability for different types of testing based on the following categories:

    Functional Testing: Covering required functionalities comprehensively.
    Performance and Load Testing: Simulating user activity patterns.
    Integration Tests: Checking the interactions between connected modules.
    Input Data Variety Testing: Exploring inputs with diverse attributes and formats.
    Edge Cases and Boundary Testing: Testing limits and unexpected scenarios.
    Compatibility Testing: Ensuring adaptability across environments.
    User Interface (GUI) Testing: Focusing on usability and responsiveness.
    Security Testing: Identifying and addressing potential vulnerabilities intelligently.

    Return the results as follows, with each test type containing a 'suitability' and 'explanation':

    Output Example:

    Functional Tests
    Suitability: High
    Explanation: Document content specify detailed functional needs, such as task creation, status tracking, and task removal.

    Performance Tests
    Suitability: Medium
    Explanation: Document content specify response time limits and task limits, but lack stress testing details.

    Integration Tests
    Suitability: Low
    Explanation: Document content mention module interactions but lack details on data flow or API calls.

    Input Data Variety Testing
    Suitability: High
    Explanation: Document content specify diverse input types, such as text, images, and files, for testing.

    Edge Cases and Boundary Testing
    Suitability: High
    Explanation: Document content specify boundary conditions and error scenarios for thorough testing.

    Compatibility Testing
    Suitability: Medium
    Explanation: Document content mention browser compatibility but lack details on OS or device testing.

    User Interface (GUI) Testing
    Suitability: High
    Explanation: Document content specify UI elements, layouts, and user interactions for testing.

    Security Tests
    Suitability: Medium
    Explanation: Document content mention secure data storage and unauthorized access prevention, but lack details on encryption or audit logging.

    This analysis will help determine the document's suitability for various types of testing.
    """

    # Add the document content to the prompt
    prompt += "\n Document Content \n" + document

    # Analyze the document content using the llama3.2 model
    # Try to connect with the LLM and analyze the document. 
    # If there is a connection problem, it will handle it.
    try:
        llm = Ollama(model="llama3.2", request_timeout=300.0, json_mode=False)
        resp = llm.complete(prompt)
        return resp.text
    # If there is a connection error or timeout, return an error message
    except (ConnectionError, Timeout) as e:
        return (f"Connection error or timeout occurred: {e}")
    # If there is an unexpected error, return an error message
    except Exception as e:
        return (f"An unexpected error occurred: {e}")
