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

# Process Title'ı kaydetme butonu
if st.button("Save Process Title"):
    if not process_title:
        st.warning("Please enter a process title before saving.")
    else:
        # Sessions koleksiyonunu al
        sessions_collection = get_sessions_collection()
        
        # Veri tabanında aynı isme sahip bir işlem olup olmadığını kontrol edin
        existing_process = sessions_collection.find_one({"process_title": process_title})
        
        if existing_process:
            st.warning("A process with the same title already exists. Please choose a different title.")
        else:
            # Process Title'ı oturum özelinde kaydet
            sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"process_title": process_title}},
                upsert=True
            )
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
        document_content = read_txt(uploaded_file)
        with st.expander('Text File Content'):
            st.text(document_content)
    elif ext == 'docx':
        document_content = read_docx(uploaded_file)
        with st.expander('DOCX File Content'):
            st.text(document_content)
    elif ext == 'xlsx':
        df = read_xlsx(uploaded_file)
        with st.expander('Excel File Data'):
            st.dataframe(df)
    elif ext == 'py':
        document_content = read_python(uploaded_file)
        with st.expander('Python File Content'):
            st.code(document_content, language='python')
    else:
        st.error('Unsupported file type.')

# Document content analyse
# İlk olarak session_state içinde analyse_content anahtarını kontrol edin
if "analyse_content" not in st.session_state:
    st.session_state.analyse_content = None

# Düğmeye tıklandığında analiz işlemi
st.write("### Document Analyse")
st.write("Analyse the document content to choose the correct test type.")
if st.button("Analyse Document", key="analyse_document_content"):
    if not document_content:
        st.error("Please upload a file before analyzing the document content.")
    else:
        st.write(" document content...")
        st.session_state.analyse_content = analyse_document(document_content)
        st.success("Document content analysed successfully!")

# Analiz edilmiş içeriği göster
if st.session_state.analyse_content:
    with st.expander("Analysis Result", expanded=False):
        st.write(st.session_state.analyse_content)

st.write("### Document Type")
# Document Type selection
document_type = st.selectbox("Select the Document Type", ["--Please Select a Type--","Source Code","Test Scenario", "Test Plan", "Technical Design Document", "Requirements Document", "Use Case Document","Treaceability Matrix", "Other"], key="document_type_selection")
if st.button("Save Document Type", key="save_document_type"):
    if not "--Please Select a Type--" in document_type:
        # Save the document type to the database
        # Sessions koleksiyonunu al
        sessions_collection = get_sessions_collection()
        
        # Process Title'ı oturum özelinde kaydet
        sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"document_type": document_type}},
            upsert=True
            )
        st.success("Document Type saved successfully!")
    else:
        st.error("Please select a document type.")

# Test Types Table
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

# Test Category Selection
category_names = ["--Please Select a Category--", "Functional", "Non-Functional"]
selected_category = st.selectbox("Select a Test Category", category_names, key="category_selection")

# Filter test names based on selected category
if selected_category != "--Please Select a Category--":
    # Fetch all test names
    test_names = fetch_test_names()
    # Filter test names based on the category
    filtered_test_names = [
        test["name"] for test in test_names if test["category"] == selected_category
    ]
    filtered_test_names.insert(0, "--Please Select a Test Type--")
else:
    filtered_test_names = ["--Please Select a Test Type--"]

# Test Type Selection
selected_test_name = st.selectbox("Select a Test Type to Generate Test Scenarios", filtered_test_names, key="test_name_selection")

# Display selected test type
if selected_test_name != "--Please Select a Test Type--":
    st.write(f"You selected: **{selected_test_name}**")



# # Test selection
# test_names = fetch_test_names()
# test_names.insert(0, "--Please Select a Test Type--")
# selected_test_name = st.selectbox("Select a Test Type to Generate Test Scenarios", test_names, key="test_name_selection")

# Fetch and display test scenario data based on selection
if selected_test_name:
    scenario_data = fetch_scenario_from_db(selected_test_name, session_id=session_id)

    # if scenario_data and document_type != "--Please Select a Type--" and document_content and process_title:
    #     st.write("### Initial Prompt")
    #     test_prompt = scenario_data.get("test_prompt", "No test prompt available.")
    #     if test_prompt:
    #         customised_prompt = generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt)
    #         if customised_prompt:
    #             update_scenario_in_db(selected_test_name, {"test_prompt": customised_prompt}, session_id=session_id)
    #             st.success("Initial prompt updated in original_prompts!")


    #     else:
    #         st.warning("No initial prompt available.")

        # # Optionally, display the initial test prompt
        # with st.expander("Initial Prompt Text", expanded=False):
        #     editable_prompt = st.session_state.get("editable_prompt", False)
        #     if editable_prompt:
        #         test_prompt = st.text_area("Test Prompt", scenario_data.get("test_prompt", ""), height=150)
        #     else:
        #         st.write(test_prompt)

        #     # Edit and Save buttons
        #     col1_prompt, col2_prompt = st.columns(2)
        #     with col1_prompt:
        #         if st.button("Edit Prompt", key="edit_prompt", disabled=editable_prompt):
        #             st.session_state["editable_prompt"] = True
        #     with col2_prompt:
        #         if st.button("Save Prompt", key="save_prompt", disabled=not editable_prompt):
        #             update_scenario_in_db(selected_test_name, {"test_prompt": test_prompt}, session_id=session_id)
        #             st.success("Prompt saved successfully!")
        #             st.session_state["editable_prompt"] = False

# CALISIYOR!!!
    if scenario_data and document_type != "--Please Select a Type--" and document_content and process_title:
        st.write("### Initial Prompt")
        
        # Initial Prompt Text - Görüntülenebilir, ancak düzenlenemez
        test_prompt = scenario_data.get("test_prompt", "No test prompt available.")
        with st.expander("Initial Prompt Text", expanded=True):
            st.write(test_prompt)
        
        if test_prompt != "No test prompt available.":
            if not scenario_data.get("customised_prompt_status", False):
                customised_prompt = generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt)
                if customised_prompt:
                    update_scenario_in_db(selected_test_name,{"test_prompt": customised_prompt, "customised_prompt_status": True},session_id=session_id)
            else:
                customised_prompt = scenario_data.get("customised_prompt", "No customised prompt available.")
                if customised_prompt != "No customised prompt available.":

                    with st.expander("Customised Prompt Text", expanded=True):
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

# DUZENLENECEK
# # İlk olarak bir flag tanımlayın
# if "reload_page" not in st.session_state:
#     st.session_state["reload_page"] = False

# # Eğer reload_page True ise, sayfayı yeniden başlat
# if st.session_state["reload_page"]:
#     st.session_state["reload_page"] = False  # Bayrağı sıfırla
#     st.experimental_set_query_params(reloaded_item="true")  # URL parametresi ekle veya düzenle

# if scenario_data and document_type != "--Please Select a Type--" and document_content and process_title:
#     st.write("### Initial Prompt")
    
#     # Initial Prompt Text - Görüntülenebilir
#     test_prompt = scenario_data.get("test_prompt", "No test prompt available.")
#     with st.expander("Initial Prompt Text", expanded=False):
#         st.write(test_prompt)
    
#     if test_prompt != "No test prompt available.":
#         # Customised Prompt oluşturma ya da veritabanından getirme
#         customised_prompt = scenario_data.get("customised_prompt", None)
#         if not customised_prompt:
#             customised_prompt = generate_customise_base_prompt(selected_test_name, document_type, document_content, test_prompt)
#             if customised_prompt:
#                 update_scenario_in_db(
#                     selected_test_name,
#                     {"customised_prompt": customised_prompt, "customised_prompt_status": True},
#                     session_id=session_id
#                 )
#                 st.session_state["reload_page"] = True  # Sayfa yenileme bayrağını ayarla
#                 st.experimental_set_query_params(reloaded_item="true")  # Parametreyi güncelle

#         # Customised Prompt'u göster ve düzenleme/kaydetme imkanı sun
#         st.write("### Customised Prompt")
#         with st.expander("Customised Prompt Text", expanded=False):
#             editable_prompt = st.session_state.get("editable_customised_prompt", False)
            
#             if editable_prompt:
#                 customised_prompt = st.text_area("Edit Customised Prompt", customised_prompt, height=150)
#             else:
#                 st.write(customised_prompt)
            
#             # Düzenleme ve Kaydetme butonları
#             col1_prompt, col2_prompt = st.columns(2)
#             with col1_prompt:
#                 if st.button("Edit Customised Prompt", key="edit_customised_prompt", disabled=editable_prompt):
#                     st.session_state["editable_customised_prompt"] = True
#             with col2_prompt:
#                 if st.button("Save Customised Prompt", key="save_customised_prompt", disabled=not editable_prompt):
#                     if customised_prompt:
#                         update_scenario_in_db(
#                             selected_test_name,
#                             {"customised_prompt": customised_prompt},
#                             session_id=session_id
#                         )
#                         st.success("Customised prompt saved successfully!")
#                         st.session_state["editable_customised_prompt"] = False

        st.write("### You can")
        st.markdown("""
        - Edit the prompt and add more details.
        - Select the instruction elements and scoring elements you want to edit.
        - Select an LLM model for the test scenario generation.
        ---
        """)

        st.subheader(f"Details for {selected_test_name}")

        # First Part: Instruction Elements
        st.write("### Instruction Elements")
        test_instruction_elements = scenario_data.get("test_instruction_elements_and_prompts", {})

        if test_instruction_elements:
            # Display instruction element names as checkboxes in two columns
            col1, col2 = st.columns(2)
            selected_instruction_elements = {}
            instruction_element_names = list(test_instruction_elements.keys())

            for i, name in enumerate(instruction_element_names):
                if i % 2 == 0:
                    with col1:
                        selected = st.checkbox(name, key=f"checkbox_instruction_{name}")
                else:
                    with col2:
                        selected = st.checkbox(name, key=f"checkbox_instruction_{name}")
                selected_instruction_elements[name] = selected

            # Display selected instruction elements in expanders
            for name, selected in selected_instruction_elements.items():
                if selected:
                    editable_key = f"editable_instruction_{name}"
                    with st.expander(f"{name}", expanded=False):
                        editable = st.session_state.get(editable_key, False)
                        content = test_instruction_elements.get(name, "")
                        if editable:
                            updated_content = st.text_area(f"{name}", value=content, height=100)
                        else:
                            st.write(content)

                        # Edit and Save buttons
                        col1_exp, col2_exp = st.columns(2)
                        with col1_exp:
                            if st.button(f"Edit {name}", key=f"edit_instruction_{name}", disabled=editable):
                                st.session_state[editable_key] = True

                        with col2_exp:
                            if st.button(f"Save {name}", key=f"save_instruction_{name}", disabled=not editable):
                                # updated_content'in tanımlı olup olmadığını kontrol ediyoruz
                                updated_content = st.session_state.get("updated_content", None)

                                # Yalnızca `updated_content` mevcutsa güncelleme yap
                                if updated_content:
                                    test_instruction_elements[name] = updated_content
                                    update_scenario_in_db(
                                        selected_test_name, 
                                        {"test_instruction_elements_and_prompts": test_instruction_elements}, 
                                        session_id=session_id
                                    )
                                    st.success(f"{name} saved successfully!")
                                    # Save butonunu inaktif yap, Edit butonunu aktif yap
                                    st.session_state[editable_key] = False
                                else:
                                    st.error("Content does not change before the last save.")
        else:
            st.write("No instruction elements available.")

        # Second Part: Scoring Elements
        st.write("### Scoring Elements")
        test_scoring_elements = scenario_data.get("test_scoring_elements_and_prompts", {})

        if test_scoring_elements:
            # Display scoring element names as checkboxes in two columns
            col1, col2 = st.columns(2)
            selected_scoring_elements = {}
            scoring_element_names = list(test_scoring_elements.keys())

            for i, name in enumerate(scoring_element_names):
                if i % 2 == 0:
                    with col1:
                        selected = st.checkbox(name, key=f"checkbox_scoring_{name}")
                else:
                    with col2:
                        selected = st.checkbox(name, key=f"checkbox_scoring_{name}")
                selected_scoring_elements[name] = selected

            # Display selected scoring elements in expanders
            for name, selected in selected_scoring_elements.items():
                if selected:
                    editable_key = f"editable_scoring_{name}"
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
                                # updated_content'in tanımlı olup olmadığını kontrol ediyoruz
                                updated_content = st.session_state.get("updated_content", None)

                                # Yalnızca `updated_content` mevcutsa güncelleme yap
                                if updated_content:
                                    test_scoring_elements[name] = updated_content
                                    update_scenario_in_db(
                                        selected_test_name, 
                                        {"test_scoring_elements_and_prompts": test_scoring_elements}, 
                                        session_id=session_id
                                    )
                                    st.success(f"{name} saved successfully!")
                                    # Save butonunu inaktif yap, Edit butonunu aktif yap
                                    st.session_state[editable_key] = False
                                else:
                                    st.error("Content does not change before the last save.")
        else:
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
                
                st.success("Prompt generated successfully!")
                
                # Save the generated prompt to session_state
                st.session_state["combined_prompt"] = combined_prompt
                
                # Save the generated prompt to the database
                save_generated_prompt(session_id, combined_prompt)

                # Display the generated prompt in the UI
                with st.expander("Generated Prompt"):
                    st.text_area("Prompt", combined_prompt, height=200)

        # Run Model button
        if st.button("Run Model on Generated Prompt"):
            # Check if combined_prompt is available in session_state
            if "combined_prompt" in st.session_state:
                combined_prompt = st.session_state["combined_prompt"]
                model_output = run_model_on_prompt(selected_llm_model, combined_prompt)
                
                if model_output:
                    # Show the model output
                    with st.expander("Model Output", expanded=True):
                        st.write(model_output)
                    # Save the model output to the database
                    save_model_output_to_db(session_id, model_output, db)
                    st.success("Model run successfully and output saved to database!")
                else:
                    st.error("Model output validation failed.")
            else:
                st.warning("Please generate a prompt before running the model.")
        
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
        #             # model_output değerini veri tabanından al
        #             model_output = scenario_data.get("model_output", "Model output can not be found.")
        #             if not model_output:
        #                 st.warning("Model output not found in the database. Please run the model first.")
        #             else:
        #                 # Judge kombinasyonunu oluştur ve model output ile birleştir
        #                 judge_combined_prompt += "\n Apply the above mentioned judge elements to the model output. \n" + model_output
                        
        #                 # run_judge_on_prompt fonksiyonunu çalıştır ve judge_output'u al
        #                 judge_output = run_judge_on_prompt(judge_combined_prompt, uploaded_file)
                        
        #                 if judge_output:
        #                     # Judge çıktısını veri tabanına aynı document içinde kaydet
        #                     update_scenario_in_db(
        #                         selected_test_name, 
        #                         {"judge_output": judge_output}, 
        #                         session_id=session_id
        #                     )
        #                     st.success("Judge has been run and output saved to database.")
                            
        #                     # Judge çıktısını kullanıcıya göster
        #                     with st.expander("Judge Output", expanded=True):
        #                         st.write(judge_output)
        #                 else:
        #                     st.error("Judge output validation failed.")
        #         else:
        #             st.warning("Please select at least one judge element to run.")
        
        # Test Case Creation Prompt with Editable Structure
        st.write("### Test Case Creation Prompt")
        with st.expander("Test Case Prompt", expanded=False):
            editable_test_case_prompt = st.session_state.get("editable_test_case_prompt", False)

            if editable_test_case_prompt:
                updated_test_case_main_prompt = st.text_area(
                    "Edit Test Case Prompt", 
                    scenario_data.get("test_case_main_prompt", ""), 
                    height=150
                )
            else:
                st.write(scenario_data.get("test_case_main_prompt", ""))

            # Edit and Save buttons
            col1_prompt, col2_prompt = st.columns(2)
            with col1_prompt:
                if st.button("Edit Test Case Prompt", key="edit_test_case_prompt", disabled=editable_test_case_prompt):
                    st.session_state["editable_test_case_prompt"] = True
            with col2_prompt:
                if st.button("Save Test Case Prompt", key="save_test_case_prompt", disabled=not editable_test_case_prompt):
                    update_scenario_in_db(
                        selected_test_name, 
                        {"test_case_main_prompt": updated_test_case_main_prompt}, 
                        session_id=session_id
                    )
                    st.success("Test Case Prompt saved successfully!")
                    st.session_state["editable_test_case_prompt"] = False

        # Test Case Types Selection
        st.write("### Select Test Case Types")
        test_case_prompts = scenario_data.get("test_case_create_prompts", {})
        selected_test_cases = {}

        col1, col2 = st.columns(2)
        for i, (test_case, prompt) in enumerate(test_case_prompts.items()):
            with (col1 if i % 2 == 0 else col2):
                selected_test_cases[test_case] = st.checkbox(test_case)

        # Display Selected Test Case Prompts
        for test_case, is_selected in selected_test_cases.items():
            if is_selected:
                with st.expander(f"{test_case} Prompt", expanded=False):
                    prompt_text = test_case_prompts[test_case]
                    editable_prompt = st.text_area(f"Edit {test_case} Prompt", prompt_text, height=150)
                    if st.button(f"Save {test_case} Prompt"):
                        test_case_prompts[test_case] = editable_prompt
                        update_scenario_in_db(selected_test_name, {"test_case_create_prompts": test_case_prompts}, session_id=session_id)
                        st.success(f"{test_case} Prompt updated successfully!")

        # Display the section title for Test Case Generation
        st.write("### Select an LLM Model")

        # Test Case Generation Model Selection
        test_case_generation_model = st.selectbox("Select an LLM model:", llm_models, key="test_case_generation_model")
        
        if st.button("Create Test Scenarios"):
            # MongoDB'den model_output alın
            model_output = fetch_model_output_from_db(session_id)
            if not model_output:
                st.warning("Model output not found in the database. Please run the model first.")
            else:
                # Test senaryolarını model_output'tan alın
                test_scenarios = model_output.get("TestScenarios", [])

                # Kullanıcının düzenlediği test_case_main_prompt değerini alın
                test_case_main_prompt = st.session_state.get(
                    "updated_test_case_main_prompt",
                    scenario_data.get("test_case_main_prompt", "")
                )

                generated_test_cases = []
                test_case_json_structure = generate_json_structure()

                # Model output içindeki her senaryo için işlem yap
                for scenario in test_scenarios:
                    # Tüm değerleri string olarak birleştir
                    scenario_details = "\n".join(f"{key}: {value}" for key, value in scenario.items())

                    # Seçilen test türlerini birleştir
                    combined_prompts = []
                    for test_case_type, is_selected in selected_test_cases.items():
                        if is_selected:
                            specific_prompt = test_case_prompts.get(test_case_type, "")
                            combined_prompts.append(f"Test Case Type: {test_case_type}\n{specific_prompt}")
                    
                    # Tek bir prompt oluştur
                    scenario_details_text = f"Scenario Details:\n{scenario_details}"

                    # Combined prompts için birleştirme işlemini ayrı yapın
                    combined_prompts_text = "Combined Test Case Prompts:\n" + "\n\n".join(combined_prompts)

                    # JSON yapısını string'e çevirin
                    test_case_structure_text = str(test_case_json_structure)

                    # Tüm parçaları birleştirin
                    combined_prompt = (
                        f"{test_case_main_prompt}\n\n"
                        f"{scenario_details_text}\n\n"
                        f"{combined_prompts_text}\n\n"
                        f"{test_case_structure_text}\n\n"
                    )

                    # LLM üzerinden test case output alın
                    try:
                        test_case_llm_output_json = generate_test_case(test_case_generation_model, combined_prompt, max_retries=3)
                    except Exception as e:
                        st.error(f"An error occurred while generating test case from LLM: {e}")
                        test_case_llm_output_json = {"error": "Failed to generate test case"}

                    # Test durumu veritabanına ekle
                    test_case_data = {
                        "scenario_id": scenario.get("ScenarioID", "Unknown"),
                        "combined_prompt": combined_prompt,
                        "test_case": test_case_llm_output_json
                    }
                    generated_test_cases.append(test_case_data)

                    update_scenario_in_db(
                        selected_test_name,
                        test_case_data,
                        session_id=session_id
                    )

            # Kullanıcıya oluşturulan test durumlarını göster
            if generated_test_cases:
                st.success("Test cases created successfully and saved to the database!")
                st.write("### Generated Test Cases")
                for i, test_case in enumerate(generated_test_cases):
                    with st.expander(f"Test Case {i + 1}: Scenario ID - {test_case['scenario_id']}", expanded=False):
                        st.json(test_case["test_case"])
            else:
                st.warning("No test cases were generated. Please select at least one test case type.")

    else:
        st.info("Please provide all the required inputs!",icon="ℹ️")