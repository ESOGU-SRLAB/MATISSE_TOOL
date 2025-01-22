""" 
This script includes functions to interact with MongoDB and fetch data from it.
It includes functions to fetch test names, fetch scenarios, update scenarios, initialize session, save generated prompt and fetch model output from MongoDB.
"""

import os
from pymongo import MongoClient

# MongoDB URI from environment variable
MONGO_URI = os.getenv("MONGO_URI")
# MongoDB client and database
client = MongoClient(MONGO_URI)
db = client["modular_test_scenario_gen"]  # Database name

# getter function for database and collections
def get_db():
    """ Returns the database object """
    return db

# getter function for collections
def get_sessions_collection():
    """ Returns the sessions collection """
    return db["sessions"]

# getter function for default prompt collection
def get_default_prompts_collection():
    """ Returns the default_prompts collection """
    return db["default_prompts"]

# fetch test names from the database
def fetch_test_names():
    """ 
    get the default prompts collection
    fetch all the documents from the collection
    return the test names from the documents 
    """
    collection = get_default_prompts_collection()
    return [doc["test_name"] for doc in collection.find()]

# fetch scenario from the database
def fetch_scenario_from_db(test_name, session_id=None):
    """
    Takes the test name and session id as input and returns the scenario from the database.
    """
    collection = get_sessions_collection()
    session_data = collection.find_one({"session_id": session_id})
    if session_data:
        return next(
            (prompt for prompt in session_data.get("original_prompts", []) if prompt["test_name"] == test_name),
            None
        )

    return None

# update scenario in the database with the updated data
def update_scenario_in_db(test_name, updated_data, session_id=None):
    """
    Takes the test name, updated data and session id as input and updates the scenario in the database.
    """
    # get the sessions collection
    collection = get_sessions_collection()
    
    # find the seesion data with the session id
    # update the original prompt with the updated data
    # update the collection with the updated data
    collection.update_one(
        {
            "session_id": session_id,
            "original_prompts.test_name": test_name
        },
        {
            "$set": {
                f"original_prompts.$.{key}": value 
                for key, value in updated_data.items()
            }
        }
    )

# initialize session in the database with the session id and default prompts data from the default prompts collection
def initialize_session(session_id):
    """ initialize session with default prompts data """
    # get source collection and target collection for default prompts and sessions"""
    source_collection = get_default_prompts_collection()
    target_collection = get_sessions_collection()

    # get all the documents from the source collection
    data = list(source_collection.find())

    # if data is present, update the customised_prompt_status to False
    if data:
        for item in data:
            item["customised_prompt_status"] = False # set the customised_prompt_status to False
        # insert the data into the target collection
        session_data = {
            "session_id": session_id, # session id for the session
            "original_prompts": data, # original prompts data from the source collection
        }
        # insert the session data into the target collection
        target_collection.insert_one(session_data)

# save generated prompt in the database with the session id and the generated prompt
def save_generated_prompt(session_id, prompt):
    """ Generated prompt is saved in the database """
    # the main collection of sessions
    collection = get_sessions_collection()
    # update the collection with the generated prompt
    collection.update_one(
        {"session_id": session_id}, # find the document with the session id
        {"$set": {"generated_prompt": prompt}}, # update the generated prompt
        upsert=True # if the document does not exist, insert it
    )

# tak
def fetch_model_output_from_db(session_id):
    """
    Takes the session id as input and returns the model output from the database.

    Parameters:
    session_id (str): The session id to fetch the model output.

    Returns:
    str: The model output from the database.
    """
    collection = get_sessions_collection()
    document = collection.find_one({"session_id": session_id})
    if document and "model_output" in document:
        return document["model_output"]
    else:
        return None

# Save the model output to the database using the session ID
def save_test_cases_to_db(session_id, generated_test_cases, db):
    collection = db["sessions"]
    collection.update_one(
        {"session_id": session_id},
        {"$set": {"TestCases": generated_test_cases}},
        upsert=True
    )