""" This streamlit app is a smart test generation tool that helps users generate test scenarios based on the content of a document. """

import streamlit as st
from file_reader import read_txt, read_docx, read_xlsx, read_python
from database import fetch_test_names, fetch_scenario_from_db, update_scenario_in_db, save_generated_prompt, get_db, get_sessions_collection, fetch_model_output_from_db
from session_manager import get_session_id
from prompt_generate import generate_prompt
from run_model import run_model_on_prompt, save_model_output_to_db
from analyse_document import analyse_document
from run_judge import run_judge_on_prompt
from validate_prompt import validate_combined_prompt
from llama_index.llms.ollama import Ollama
from requests.exceptions import ConnectionError, Timeout
from generate_test_case import generate_json_structure, generate_test_case
import json
from create_special_test_prompt import generate_customise_base_prompt


# Adjusted LLM models list based on your terminal output
llm_models = [
    'llama3.2',
    'gemma2:2b',
    'qwen2.5-coder',
    'gemma2',
    'mistral',
    'codellama',
    'codegemma',
    'deepseek-coder',
    'llama3.1',
]

# Initialize session
session_id = get_session_id()

# Database connection
db = get_db()

# Set the title of the app
st.title('Smart Test')

# Process Title input
process_title = st.text_input("## Process Title", key="test_scenario_generation_process_name", placeholder="Enter the title of the process.")

# The button to save the process title
if st.button("Save Process Title"):
    if not process_title:
        st.warning("Please enter a process title before saving.")
    else:
        # Take the sessions collection
        sessions_collection = get_sessions_collection()
        
        # Check if a process with the same title already exists
        existing_process = sessions_collection.find_one({"process_title": process_title})
        
        if existing_process:
            st.warning("A process with the same title already exists. Please choose a different title.")
        else:
            # Save the process title to the database
            sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"process_title": process_title}},
                upsert=True
            )
            # Show a success message when the process title is saved
            st.success("Process Title saved successfully!")

# File uploader widget
uploaded_file = st.file_uploader("Upload file to use in smart test generation process.", type=['txt', 'docx', 'xlsx', 'py'])

# Check if a file has been uploaded
if uploaded_file is not None:
    # Extract file extension
    file_name = uploaded_file.name
    ext = file_name.split('.')[-1].lower()

    # Process the file based on its extension
    if ext == 'txt':
        # Read the content of the uploaded file as text
        document_content = read_txt(uploaded_file)

        
        with st.expander('Text File Content'): 
            st.text(document_content)
    elif ext == 'docx':
        # Read the content of the uploaded file as a docx file
        document_content = read_docx(uploaded_file)

        # Display the content of the file in an expander
        with st.expander('DOCX File Content'):
            st.text(document_content)
    elif ext == 'xlsx':
        df = read_xlsx(uploaded_file)

        # Display the content of the file in an expander
        with st.expander('Excel File Data'):
            st.dataframe(df)
    elif ext == 'py':
        document_content = read_python(uploaded_file)

        # Display the content of the file in an expander
        with st.expander('Python File Content'):
            st.code(document_content, language='python')
    else:
        # If the file type is not supported, show an error message
        st.error('Unsupported file type.')

# Document content analyse to choose the correct test type in the session state for saving
if "analyse_content" not in st.session_state:
    st.session_state.analyse_content = None

# Analyse Document Content when the button is clicked
st.write("### Document Analyse")
# Document content analysis button and function call to analyse the content of the document to choose the correct test type
st.write("Analyse the document content to choose the correct test type.")
if st.button("Analyse Document", key="analyse_document_content"):
    if not document_content:
        st.error("Please upload a file before analyzing the document content.")
    else:
        st.write(" document content...")
        st.session_state.analyse_content = analyse_document(document_content)
        st.success("Document content analysed successfully!")

# Show the analysis result in an expander if the content has been analysed
if st.session_state.analyse_content:
    # Display the analysis result in an expander
    with st.expander("Analysis Result", expanded=False):
        st.write(st.session_state.analyse_content)

# Document Type selection section
st.write("### Document Type")
# Document Type selection from the dropdown list
document_type = st.selectbox("Select the Document Type", ["--Please Select a Type--","Source Code","Test Scenario", "Test Plan", "Technical Design Document", "Requirements Document", "Use Case Document","Treaceability Matrix", "Other"], key="document_type_selection")
# Save the selected document type to the database when the button is clicked and the document type is selected from the dropdown list
if st.button("Save Document Type", key="save_document_type"):
    # Check if a document type has been selected
    if not "--Please Select a Type--" in document_type:
        # Save the document type to the database
        # Take the sessions collection
        sessions_collection = get_sessions_collection()
        # Save the document type to the database for the current session
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"document_type": document_type}},
            upsert=True
            )
        # Show a success message when the document type is saved
        st.success("Document Type saved successfully!")
    else:
        st.error("Please select a document type.")

# Test Types Table Display in an expander section to show the test types and detailed methods for creating their test scenarios
test_table = [
    {"Test Type": "Performance and Load Testing", "Category": "Non-Functional", 
     "How?": "Simulate user activity patterns"},
    {"Test Type": "Integration Testing", "Category": "Functional", 
     "How?": "Define interactions between connected modules"},
    {"Test Type": "Input Data Variety Testing", "Category": "Functional", 
     "How?": "Explore inputs with diverse attributes and formats"},
    {"Test Type": "Functional Testing", "Category": "Functional", 
     "How?": "Cover required functionalities comprehensively"},
    {"Test Type": "Edge Cases and Boundary Testing", "Category": "Functional", 
     "How?": "Test limits and unexpected scenarios"},
    {"Test Type": "Compatibility Testing", "Category": "Non-Functional", 
     "How?": "Ensure adaptability across environments"},
    {"Test Type": "User Interface (GUI) Testing", "Category": "Functional", 
     "How?": "Focus on usability and responsiveness"},
    {"Test Type": "Security Testing", "Category": "Non-Functional", 
     "How?": "Identify and address potential vulnerabilities intelligently"},
]

# Test Types Table Display in an expander section
with st.expander("Test Types Table"):
    st.write("Below is a table of various test types and detailed methods for creating their test scenarios.")
    st.table(test_table)

# Function to fetch all test names
def fetch_test_names():
    return [
        {"name": "Integration Testing", "category": "Functional"},
        {"name": "Input Data Variety Testing", "category": "Functional"},
        {"name": "Functional Testing", "category": "Functional"},
        {"name": "Edge Cases and Boundary Testing", "category": "Functional"},
        {"name": "User Interface (GUI) Testing", "category": "Functional"},
        {"name": "Performance and Load Testing", "category": "Non-Functional"},
        {"name": "Compatibility Testing", "category": "Non-Functional"},
        {"name": "Security Testing", "category": "Non-Functional"},
    ]

# Test Category Selection Dropdown List to select the test category for the test type selection in the next step of the test scenario generation process
category_names = ["--Please Select a Category--", "Functional", "Non-Functional"]
# Test Category Selection Dropdown List to select the test category for the test type selection in the next step of the test scenario generation process
selected_category = st.selectbox("Select a Test Category", category_names, key="category_selection")

# Filter test names based on selected category and display them in the next dropdown list for the test type selection
if selected_category != "--Please Select a Category--":
    # Fetch all test names from the database
    test_names = fetch_test_names()
    # Filter test names based on the category selected
    filtered_test_names = [
        test["name"] for test in test_names if test["category"] == selected_category
    ]
    # Insert a default option to the beginning of the list for the test type selection dropdown list to select a test type for the test scenario generation process
    filtered_test_names.insert(0, "--Please Select a Test Type--")
else:
    # If no category is selected, show an empty list for the test type selection dropdown list
    filtered_test_names = ["--Please Select a Test Type--"]

# Test Type Selection Dropdown List to select a test type for the test scenario generation process
selected_test_name = st.selectbox("Select a Test Type to Generate Test Scenarios", filtered_test_names, key="test_name_selection")

# Display selected test type in the UI
if selected_test_name != "--Please Select a Test Type--":
    st.write(f"You selected: **{selected_test_name}**")

# We will upgrade this part in the next steps for the initial prompt and customised prompt
# Fetch and display test scenario data based on selection
if selected_test_name:
    # Fetch the test scenario data from the database
    scenario_data = fetch_scenario_from_db(selected_test_name, session_id=session_id)
    # Check scenario data and other required fields to proceed
    if scenario_data and document_type != "--Please Select a Type--" and document_content and process_title:
        # If the customised prompt status is True, show a warning message
        if scenario_data.get("customised_prompt_status", False):
            st.warning("A customised prompt has already been created for this scenario. If you wish to initiate a new testing process, please refresh the page to start a new session.")

        # Save the selected category and test type to the database
        sessions_collection = get_sessions_collection()
        sessions_collection.update_one(
            {"session_id": session_id}, # Find the session with the session_id
            {
                "$set": {
                    "selected_category": selected_category,  # Save the selected category
                    "selected_test_type": selected_test_name  # Save the selected test type
                }
            },
            upsert=True  # If the session does not exist, create a new one
        )
        # Show a success message when the category and test type are saved
        st.success("Category and test type saved successfully!")

        # Display the initial prompt
        st.write("### Initial Prompt")
        
        # Initial Prompt Text - Show the initial prompt text in an expander
        test_prompt = scenario_data.get("test_prompt", "No test prompt available.")
        with st.expander("Initial Prompt Text", expanded=False):
            st.write(test_prompt)
        
        if test_prompt != "No test prompt available.":
            if not scenario_data.get("customised_prompt_status", False):
                customised_prompt = generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt)
                if customised_prompt:
                    update_scenario_in_db(selected_test_name,{"test_prompt": customised_prompt, "customised_prompt_status": True},session_id=session_id)
            else:
                customised_prompt = scenario_data.get("customised_prompt", "No customised prompt available.")
                if customised_prompt != "No customised prompt available.":

                    with st.expander("Customised Prompt Text", expanded=False):
                        editable_prompt = st.session_state.get("editable_prompt", False)
                        
                        if editable_prompt:
                            customised_prompt = st.text_area("Customised Prompt", customised_prompt, height=150)
                        else:
                            st.write(customised_prompt)
                        
                        # Düzenleme ve Kaydetme butonları
                        col1_prompt, col2_prompt = st.columns(2)
                        with col1_prompt:
                            if st.button("Edit Customised Prompt", key="edit_customised_prompt", disabled=editable_prompt):
                                st.session_state["editable_prompt"] = True
                        with col2_prompt:
                            if st.button("Save Customised Prompt", key="save_customised_prompt", disabled=not editable_prompt):
                                update_scenario_in_db(selected_test_name, {"test_prompt": customised_prompt}, session_id=session_id)
                                st.success("Customised prompt saved successfully!")
                                st.session_state["editable_prompt"] = False

        # Show what you can do next
        st.write("### You can")
        st.markdown("""
        - Edit the prompt and add more details.
        - Select the instruction elements and scoring elements you want to edit.
        - Select an LLM model for the test scenario generation.
        ---
        """)
        # Show details for the selected test
        st.subheader(f"Details for {selected_test_name}")

        # First Part: Instruction Elements and Prompts - İnstruction Elements
        st.write("### Instruction Elements")
        # Get the instruction elements and prompts from the scenario data
        test_instruction_elements = scenario_data.get("test_instruction_elements_and_prompts", {})

        # Check if there are any instruction elements available
        if test_instruction_elements:
            # Create two columns which include the checkboxes for the instruction elements
            col1, col2 = st.columns(2)
            selected_instruction_elements = {}
            # Get the names of the instruction elements
            instruction_element_names = list(test_instruction_elements.keys())

            # Display instruction element names as checkboxes in two columns
            for i, name in enumerate(instruction_element_names):
                if i % 2 == 0:
                    with col1:
                        selected = st.checkbox(name, key=f"checkbox_instruction_{name}")
                else:
                    with col2:
                        selected = st.checkbox(name, key=f"checkbox_instruction_{name}")
                # Save the selected instruction elements to a dictionary
                selected_instruction_elements[name] = selected

            # Display selected instruction elements in expanders
            for name, selected in selected_instruction_elements.items():
                # Check if the instruction element is selected
                if selected:
                    # Define a key for the editable state of the instruction element
                    editable_key = f"editable_instruction_{name}"
                    # Create an expander for the instruction element
                    with st.expander(f"{name}", expanded=False):
                        # Get the editable state of the instruction element
                        editable = st.session_state.get(editable_key, False)
                        # Get the content of the instruction element
                        content = test_instruction_elements.get(name, "")
                        # Check if the instruction element is editable
                        if editable:
                            updated_content = st.text_area(f"{name}", value=content, height=100)
                        # If the instruction element is not editable, display the content
                        else:
                            st.write(content)

                        # Edit and Save buttons
                        col1_exp, col2_exp = st.columns(2)
                        # Edit button
                        with col1_exp:
                            # If the Edit button is clicked, set the instruction element as editable
                            if st.button(f"Edit {name}", key=f"edit_instruction_{name}", disabled=editable):
                                st.session_state[editable_key] = True

                        # Save button
                        with col2_exp:
                            if st.button(f"Save {name}", key=f"save_instruction_{name}", disabled=not editable):
                                # Get the updated content of the instruction element
                                updated_content = st.session_state.get("updated_content", None)

                                # Update content if there is an updated content
                                if updated_content:
                                    # Update the instruction element content specified by the name
                                    test_instruction_elements[name] = updated_content
                                    # Update the instruction elements and prompts in the database
                                    update_scenario_in_db(
                                        selected_test_name, 
                                        {"test_instruction_elements_and_prompts": test_instruction_elements}, 
                                        session_id=session_id
                                    )
                                    # Show a success message when the instruction element is saved
                                    st.success(f"{name} saved successfully!")
                                    # Inactivate the Save button and activate the Edit button
                                    st.session_state[editable_key] = False
                                else:
                                    # Show an error message if the content has not changed before the last save
                                    st.error("Content does not change before the last save.")
        else:
            # Show a message if there are no instruction elements available
            st.write("No instruction elements available.")

        # Second Part: Scoring Elements
        st.write("### Scoring Elements")
        # Get the scoring elements and prompts from the scenario data
        test_scoring_elements = scenario_data.get("test_scoring_elements_and_prompts", {})

        # Check if there are any scoring elements available
        if test_scoring_elements:
            # Display scoring element names as checkboxes in two columns
            col1, col2 = st.columns(2)
            # Define a dictionary to store the selected scoring elements
            selected_scoring_elements = {}
            # Get the names of the scoring elements
            scoring_element_names = list(test_scoring_elements.keys())

            # Display scoring element names as checkboxes in two columns
            for i, name in enumerate(scoring_element_names):
                if i % 2 == 0:
                    with col1:
                        selected = st.checkbox(name, key=f"checkbox_scoring_{name}")
                else:
                    with col2:
                        selected = st.checkbox(name, key=f"checkbox_scoring_{name}")
                # Save the selected scoring elements to a dictionary
                selected_scoring_elements[name] = selected

            # Display selected scoring elements in expanders
            for name, selected in selected_scoring_elements.items():
                # Check if the scoring element is selected
                if selected:
                    # Define a key for the editable state of the scoring element
                    editable_key = f"editable_scoring_{name}"
                    # Create an expander for the scoring element
                    with st.expander(f"{name}", expanded=False):
                        editable = st.session_state.get(editable_key, False)
                        content = test_scoring_elements.get(name, "")
                        if editable:
                            updated_content = st.text_area(f"{name}", value=content, height=100)
                        else:
                            st.write(content)

                        # Edit and Save buttons
                        col1_exp, col2_exp = st.columns(2)
                        with col1_exp:
                            if st.button(f"Edit {name}", key=f"edit_scoring_{name}", disabled=editable):
                                st.session_state[editable_key] = True
                        with col2_exp:
                            if st.button(f"Save {name}", key=f"save_scoring_{name}", disabled=not editable):
                                # Get the updated content of the scoring element
                                updated_content = st.session_state.get("updated_content", None)

                                # Update content if there is an updated content
                                if updated_content:
                                    test_scoring_elements[name] = updated_content
                                    update_scenario_in_db(
                                        selected_test_name, 
                                        {"test_scoring_elements_and_prompts": test_scoring_elements}, 
                                        session_id=session_id
                                    )
                                    st.success(f"{name} saved successfully!")
                                    # Inactivate the Save button and activate the Edit button
                                    st.session_state[editable_key] = False
                                else:
                                    # Show an error message if the content has not changed before the last save
                                    st.error("Content does not change before the last save.")
        else:
            # Show a message if there are no scoring elements available
            st.write("No scoring elements available.")
        
        # Display the section title
        st.write("### Select an LLM Model")

        # Use a selectbox for model selection
        selected_llm_model = st.selectbox("Select an LLM model:", llm_models, key="llm_model_selection")

        # Display the selected model (optional)
        st.write(f"You have selected: **{selected_llm_model}**")

        # Generate Prompt button
        if st.button("Generate Prompt", key="generate_prompt"):
            is_valid, missing = validate_combined_prompt(
                process_title, 
                document_type, 
                test_prompt, 
                document_content,
                selected_test_name,
                selected_instruction_elements, 
                test_instruction_elements, 
                selected_scoring_elements, 
                test_scoring_elements
            )
            # Check if all required fields are provided
            if not is_valid:
                st.warning(f"Please provide the following missing fields: {', '.join(missing)}")
            # Check session state for prompt generation status
            if st.session_state.get("generate_prompt", False):
                # Generate the prompt
                combined_prompt = generate_prompt(
                    process_title,
                    document_type,
                    test_prompt,
                    document_content,
                    selected_test_name,
                    selected_instruction_elements, 
                    test_instruction_elements, 
                    selected_scoring_elements, 
                    test_scoring_elements
                )
                # Show the generated prompt in an expander
                st.success("Prompt generated successfully!")
                
                # Save the generated prompt to session_state
                st.session_state["combined_prompt"] = combined_prompt
                
                # Save the generated prompt to the database
                save_generated_prompt(session_id, combined_prompt)

                # Display the generated prompt in the UI for the user to see in an expander
                with st.expander("Generated Prompt"):
                    st.text_area("Prompt", combined_prompt, height=200)

        # # Run Model with Generated Prompt button
        # if st.button("Run Model on Generated Prompt"):
        #     # Check if combined_prompt is available in session_state
        #     if "combined_prompt" in st.session_state:
        #         combined_prompt = st.session_state["combined_prompt"]
        #         # Take the model output
        #         model_output = run_model_on_prompt(selected_llm_model, combined_prompt)
                
        #         # Check if the model output is available
        #         if model_output:
        #             # Show the model output
        #             with st.expander("Model Output", expanded=False):
        #                 st.write(model_output)
        #             # Save the model output to the database
        #             save_model_output_to_db(session_id, model_output, db)
        #             # Show a success message when the model output is saved
        #             st.success("Model run successfully and output saved to database!")
        #         else:
        #             st.error("Model output validation failed.")
        #     else:
        #         st.warning("Please generate a prompt before running the model.")
        # Run Model with Generated Prompt button
        if st.button("Run Model on Generated Prompt"):
            # Fetch the current session data
            current_session = db["sessions"].find_one({"session_id": session_id})
            
            # Check if a TestScenario already exists in the session
            if current_session and "model_output" in current_session and "TestScenarios" in current_session["model_output"]:
                st.warning("A test scenario already exists in this session. Please proceed to create test cases.")
            else:
                # Check if combined_prompt is available in session_state
                if "combined_prompt" in st.session_state:
                    combined_prompt = st.session_state["combined_prompt"]
                    # Take the model output
                    model_output = run_model_on_prompt(selected_llm_model, combined_prompt)
                    
                    # Check if the model output is available
                    if model_output:
                        # Show the model output
                        with st.expander("Model Output", expanded=False):
                            st.write(model_output)
                        # Save the model output to the database
                        save_model_output_to_db(session_id, {"TestScenarios": model_output["TestScenarios"]}, db)
                        # Show a success message when the model output is saved
                        st.success("Test scenario created successfully and saved to the database!")
                    else:
                        st.error("Model output validation failed.")
                else:
                    st.warning("Please generate a prompt before running the model.")

        
        # # We will upgrade this part in the next steps
        # # LLM Output Judge Elements
        # st.write("### LLM Output Judge Elements")
        # llm_output_judges = scenario_data.get("llm_output_judges_and_prompts", {})

        # if llm_output_judges:
        #     # Display LLM Output Judge element names as checkboxes in two columns
        #     col1, col2 = st.columns(2)
        #     selected_llm_judges = {}
        #     llm_judge_names = list(llm_output_judges.keys())

        #     for i, name in enumerate(llm_judge_names):
        #         if i % 2 == 0:
        #             with col1:
        #                 selected = st.checkbox(name, key=f"checkbox_llm_judge_{name}")
        #         else:
        #             with col2:
        #                 selected = st.checkbox(name, key=f"checkbox_llm_judge_{name}")
        #         selected_llm_judges[name] = selected

        #     # Display selected LLM Output Judge elements in expanders
        #     for name, selected in selected_llm_judges.items():
        #         if selected:
        #             editable_key = f"editable_llm_judge_{name}"
        #             with st.expander(f"{name}", expanded=False):
        #                 editable = st.session_state.get(editable_key, False)
        #                 judge_content = llm_output_judges.get(name, "")
        #                 if editable:
        #                     updated_judge_content = st.text_area(f"{name}", value=judge_content, height=100)
        #                 else:
        #                     st.write(judge_content)

        #                 # Edit and Save buttons
        #                 col1_exp, col2_exp = st.columns(2)
        #                 with col1_exp:
        #                     if st.button(f"Edit {name}", key=f"edit_llm_judge_{name}", disabled=editable):
        #                         st.session_state[editable_key] = True
        #                 with col2_exp:
        #                     if st.button(f"Save {name}", key=f"save_llm_judge_{name}", disabled=not editable):
        #                         # Update only this specific LLM Output Judge element
        #                         llm_output_judges[name] = updated_judge_content
        #                         update_scenario_in_db(selected_test_name, {"llm_output_judges_and_prompts": llm_output_judges}, session_id=session_id)
        #                         st.success(f"{name} saved successfully!")
        #                         st.session_state[editable_key] = False

        #     # Run Judge button
        #     selected_judge_values = [value for name, value in llm_output_judges.items() if selected_llm_judges.get(name)]
        #     judge_combined_prompt = "\n".join(selected_judge_values)

        #     if st.button("Run Judge"):
        #         if judge_combined_prompt:
        #             # Retrieve the model_output value from the database
        #             model_output = scenario_data.get("model_output", "Model output cannot be found.")
        #             if not model_output:
        #                 st.warning("Model output not found in the database. Please run the model first.")
        #             else:
        #                 # Create a judge combination and merge it with the model output
        #                 judge_combined_prompt += "\n Apply the above-mentioned judge elements to the model output. \n" + model_output
                        
        #                 # Run the run_judge_on_prompt function and get the judge_output
        #                 judge_output = run_judge_on_prompt(judge_combined_prompt, uploaded_file)
                        
        #                 if judge_output:
        #                     # Save the judge output in the database within the same document
        #                     update_scenario_in_db(
        #                         selected_test_name, 
        #                         {"judge_output": judge_output}, 
        #                         session_id=session_id
        #                     )
        #                     st.success("Judge has been run and output saved to database.")
                            
        #                     # Display the judge output to the user
        #                     with st.expander("Judge Output", expanded=False):
        #                         st.write(judge_output)
        #                 else:
        #                     st.error("Judge output validation failed.")
        #         else:
        #             st.warning("Please select at least one judge element to run.")
        
        # Test Case Creation Prompt with Editable Structure
        st.write("### Test Case Creation Prompt")
        with st.expander("Test Case Prompt", expanded=False):
            # Get the editable state of the test case prompt
            editable_test_case_prompt = st.session_state.get("editable_test_case_prompt", False)
            # Check if the test case prompt is editable
            if editable_test_case_prompt:
                updated_test_case_main_prompt = st.text_area(
                    "Edit Test Case Prompt", 
                    scenario_data.get("test_case_main_prompt", ""), 
                    height=150
                )
            # If the test case prompt is not editable, display the content
            else:
                st.write(scenario_data.get("test_case_main_prompt", ""))

            # Edit and Save buttons for the test case prompt
            col1_prompt, col2_prompt = st.columns(2)
            with col1_prompt:
                # If the Edit button is clicked, set the test case prompt as editable
                if st.button("Edit Test Case Prompt", key="edit_test_case_prompt", disabled=editable_test_case_prompt):
                    # Set the editable state of the test case prompt
                    st.session_state["editable_test_case_prompt"] = True
            with col2_prompt:
                # If the Save button is clicked, save the updated test case prompt
                if st.button("Save Test Case Prompt", key="save_test_case_prompt", disabled=not editable_test_case_prompt):
                    # Get the updated test case prompt
                    update_scenario_in_db(
                        selected_test_name, 
                        {"test_case_main_prompt": updated_test_case_main_prompt}, 
                        session_id=session_id
                    )
                    # Show a success message when the test case prompt is saved
                    st.success("Test Case Prompt saved successfully!")
                    # Inactivate the Save button and activate the Edit button
                    st.session_state["editable_test_case_prompt"] = False

        # Test Case Types Selection
        st.write("### Select Test Case Types")
        # Get the test case prompts from the scenario data
        test_case_prompts = scenario_data.get("test_case_create_prompts", {})
        # Define a dictionary to store the selected test cases
        selected_test_cases = {}

        # Display test case types as checkboxes in two columns for selection
        col1, col2 = st.columns(2)
        for i, (test_case, prompt) in enumerate(test_case_prompts.items()):
            with (col1 if i % 2 == 0 else col2):
                # Create a checkbox for each test case type and store the selected state in the dictionary
                selected_test_cases[test_case] = st.checkbox(test_case)

        # Display Selected Test Case Prompts
        for test_case, is_selected in selected_test_cases.items():
            # Check if the test case is selected and display the prompt in an expander
            if is_selected:
                # Create an expander for each selected test case type and display the prompt inside it
                with st.expander(f"{test_case} Prompt", expanded=False):
                    # Get the prompt text for the test case
                    prompt_text = test_case_prompts[test_case]
                    # Create a text area for the user to edit the prompt
                    editable_prompt = st.text_area(f"Edit {test_case} Prompt", prompt_text, height=150)
                    if st.button(f"Save {test_case} Prompt"):
                        # Save the updated prompt to the database for the selected test case
                        test_case_prompts[test_case] = editable_prompt
                        # Update the test case prompt in the database
                        update_scenario_in_db(selected_test_name, {"test_case_create_prompts": test_case_prompts}, session_id=session_id)
                        # Show a success message when the prompt is saved
                        st.success(f"{test_case} Prompt updated successfully!")

        # Display the section title for Test Case Generation
        st.write("### Select an LLM Model")

        # Test Case Generation Model Selection
        test_case_generation_model = st.selectbox("Select an LLM model:", llm_models, key="test_case_generation_model")
        
        # Create Test Case Button
        if st.button("Create Test Case"):
            # Check if the model output is available in the database
            model_output = fetch_model_output_from_db(session_id)
            # Check if the model output is available
            if not model_output:
                # Show a warning message if the model output is not found
                st.warning("Model output not found in the database. Please run the model first.")
            else:
                # Get the test scenarios from the model output
                test_scenarios = model_output.get("TestScenarios", [])

                # Get the updated test case main prompt
                test_case_main_prompt = st.session_state.get(
                    "updated_test_case_main_prompt",
                    scenario_data.get("test_case_main_prompt", "")
                )

                # Define a list to store the generated test cases
                generated_test_cases = []
                # Call the generate_json_structure function to get the JSON structure for the test case
                test_case_json_structure = generate_json_structure()

            #     # Iterate over the test scenarios and generate test cases
            #     for scenario in test_scenarios:
            #         # Merge all the details into a single string
            #         scenario_details = "\n".join(f"{key}: {value}" for key, value in scenario.items())

            #         # Combine the selected test case prompts
            #         combined_prompts = []
            #         # Iterate over the selected test cases and add the prompts to the list
            #         for test_case_type, is_selected in selected_test_cases.items():
            #             # Check if the test case type is selected
            #             if is_selected:
            #                 # Get the specific prompt for the test case type
            #                 specific_prompt = test_case_prompts.get(test_case_type, "")
            #                 # Add the test case type and specific prompt to the combined prompts list
            #                 combined_prompts.append(f"Test Case Type: {test_case_type}\n{specific_prompt}")
                    
            #         # Create a prompt for the scenario details
            #         scenario_details_text = f"Scenario Details:\n{scenario_details}"

            #         # For combined prompts, perform the merging process separately
            #         combined_prompts_text = "Combined Test Case Prompts:\n" + "\n\n".join(combined_prompts)

            #         # Convert the JSON structure to a string
            #         test_case_structure_text = str(test_case_json_structure)

            #         # Merge all the prompts and details into a single prompt
            #         combined_prompt = (
            #             f"{test_case_main_prompt}\n\n"
            #             f"{scenario_details_text}\n\n"
            #             f"{combined_prompts_text}\n\n"
            #             f"{test_case_structure_text}\n\n"
            #         )

            #         # Try to generate a test case from the LLM and handle exceptions
            #         try:
            #             # Generate a test case from the combined prompt using the LLM model
            #             test_case_llm_output_json = generate_test_case(test_case_generation_model, combined_prompt, max_retries=3)
            #         except Exception as e:
            #             # Show an error message if an exception occurs during test case generation from LLM
            #             st.error(f"An error occurred while generating test case from LLM: {e}")
            #             # Set the test case LLM output to an error message
            #             test_case_llm_output_json = {"error": "Failed to generate test case"}

            #         # Save the generated test case to the database
            #         test_case_data = {
            #             "scenario_id": scenario.get("ScenarioID", "Unknown"),
            #             "combined_prompt": combined_prompt,
            #             "test_case": test_case_llm_output_json
            #         }
            #         # Append the generated test case to the list
            #         generated_test_cases.append(test_case_data)

            #         # Update the scenario in the database with the generated test case
            #         update_scenario_in_db(
            #             selected_test_name,
            #             test_case_data,
            #             session_id=session_id
            #         )

            # # Show a success message if test cases are generated successfully
            # if generated_test_cases:
            #     st.success("Test cases created successfully and saved to the database!")
            #     # Display the generated test cases in expanders
            #     st.write("### Generated Test Cases")
            #     # Iterate over the generated test cases and display them in expanders
            #     for i, test_case in enumerate(generated_test_cases):
            #         # Create an expander for each test case and display the test case inside it
            #         with st.expander(f"Test Case {i + 1}: Scenario ID - {test_case['scenario_id']}", expanded=False):
            #             st.json(test_case["test_case"])
            # else:
            #     # Show a warning message if no test cases are generated
            #     st.warning("No test cases were generated. Please select at least one test case type.")
            # Iterate over the test scenarios and generate test cases
            for scenario in test_scenarios:
                # Merge all the details into a single string
                scenario_details = "\n".join(f"{key}: {value}" for key, value in scenario.items())

                # Combine the selected test case prompts
                combined_prompts = []
                for test_case_type, is_selected in selected_test_cases.items():
                    if is_selected:
                        specific_prompt = test_case_prompts.get(test_case_type, "")
                        combined_prompts.append(f"Test Case Type: {test_case_type}\n{specific_prompt}")

                scenario_details_text = f"Scenario Details:\n{scenario_details}"
                combined_prompts_text = "Combined Test Case Prompts:\n" + "\n\n".join(combined_prompts)
                test_case_structure_text = str(test_case_json_structure)

                # Merge all prompts into a single combined prompt
                combined_prompt = (
                    f"{test_case_main_prompt}\n\n"
                    f"{scenario_details_text}\n\n"
                    f"{combined_prompts_text}\n\n"
                    f"{test_case_structure_text}\n\n"
                )

                try:
                    test_case_llm_output_json = generate_test_case(test_case_generation_model, combined_prompt, max_retries=3)
                except Exception as e:
                    st.error(f"An error occurred while generating test case from LLM: {e}")
                    test_case_llm_output_json = {"error": "Failed to generate test case"}

                test_case_data = {
                    "scenario_id": scenario.get("ScenarioID", "Unknown"),
                    "combined_prompt": combined_prompt,
                    "test_case": test_case_llm_output_json,
                }

                generated_test_cases.append(test_case_data)

            # Save `TestScenarios` and `TestCases` in `model_output`
            model_output_to_save = {
                "TestScenarios": test_scenarios,  # Assuming `test_scenarios` contains original scenario details
                "TestCases": generated_test_cases,  # Assuming `generated_test_cases` contains test case outputs
            }

            # Call the updated save function to save in the 'sessions' collection
            save_model_output_to_db(session_id, model_output_to_save, db)

            # Confirmation message
            if generated_test_cases:
                st.success("Test cases created successfully and saved to the database!")
                st.write("### Generated Test Cases")
                for i, test_case in enumerate(generated_test_cases):
                    with st.expander(f"Test Case {i + 1}: Scenario ID - {test_case['scenario_id']}", expanded=False):
                        st.json(test_case["test_case"])
            else:
                st.warning("No test cases were generated. Please select at least one test case type.")



    else:
        # Show a warning message if the required fields are not provided
        st.info("Please provide all the required inputs!",icon="ℹ️")