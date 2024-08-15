import streamlit as st
import json
from langchain_community.llms import Ollama
from requests.exceptions import ConnectionError, Timeout
from src.json_extractor import extract_and_save_json
import pandas as pd

# Define the default prompts directly in the script
default_prompts = {
    "deepseek-coder": "The main and only mission is 'Creating Test Plan using information taking from other documents like python code, requirements, etc.' Create a test plan as a table (including rows and columns) using the given file as a reference, while taking into account the technical design, requirements specification, use case, traceability matrix, and test cases. Detect and refine any gaps or areas that require adjustments. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Traceability Matrix: {trace_matrix}. Test Cases: {test_cases}. Prior Feedback: {feedback}",
    "codegemma": "The main and only mission is 'Creating Test Plan using information taking from other documents like python code, requirements, etc.' Create a test plan as a table (including rows and columns) using the given file as a reference, while taking into account the technical design, requirements specification, use case, traceability matrix, and test cases. Detect and refine any gaps or areas that require adjustments. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Traceability Matrix: {trace_matrix}. Test Cases: {test_cases}. Prior Feedback: {feedback}",
    "codellama": "The main and only mission is 'Creating Test Plan using information taking from other documents like python code, requirements, etc.' Create a test plan as a table (including rows and columns) using the given file as a reference, while taking into account the technical design, requirements specification, use case, traceability matrix, and test cases. Detect and refine any gaps or areas that require adjustments. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Traceability Matrix: {trace_matrix}. Test Cases: {test_cases}. Prior Feedback: {feedback}",
    "llama3.1": "The main and only mission is 'Creating Test Plan using information taking from other documents like python code, requirements, etc.' Create a test plan as a table (including rows and columns) using the given file as a reference, while taking into account the technical design, requirements specification, use case, traceability matrix, and test cases. Detect and refine any gaps or areas that require adjustments. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Traceability Matrix: {trace_matrix}. Test Cases: {test_cases}. Prior Feedback: {feedback}",
    "mathstral": "The main and only mission is 'Creating Test Plan using information taking from other documents like python code, requirements, etc.' Create a test as a table (including rows and columns) plan using the given file as a reference, while taking into account the technical design, requirements specification, use case, traceability matrix, and test cases. Detect and refine any gaps or areas that require adjustments. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Traceability Matrix: {trace_matrix}. Test Cases: {test_cases}. Prior Feedback: {feedback}"
}

# Define the model options
model_options = {
    "DeepSeek Coder": "deepseek-coder", #1.3 B
    "CodeGemma": "codegemma", #7 B
    "CodeLLaMa": "codellama", #7 B
    "LLaMa 3.1": "llama3.1", #8 B
    "MathStral": "mathstral" # 7 B
}

# Initialize the models
models = {
    "codegemma": Ollama(model="codegemma"),
    "codellama": Ollama(model="codellama"),
    "llama3.1": Ollama(model="llama3.1"),
    "deepseek-coder": Ollama(model="deepseek-coder"),
    "mathstral": Ollama(model="mathstral")
}

# Initialize session state for custom prompts and outputs if not already present
if "custom_prompts" not in st.session_state:
    st.session_state.custom_prompts = {}
if "outputs" not in st.session_state:
    st.session_state.outputs = []
if "suggestion_output" not in st.session_state:
    st.session_state.suggestion_output = ""
if "max_levels" not in st.session_state:
    st.session_state.max_levels = 2
if "depth" not in st.session_state:
    st.session_state.depth = 1
if "configure_models" not in st.session_state:
    st.session_state.configure_models = False
if "apply_suggestion" not in st.session_state:
    st.session_state.apply_suggestion = False
if "final_output_saved" not in st.session_state:
    st.session_state.final_output_saved = False
if "review_completed" not in st.session_state:
    st.session_state.review_completed = False
if "level_output_saved" not in st.session_state:
    st.session_state.level_output_saved = {}

# Title and Introduction
st.title("Test Planning with Chain of Thought (CoT) and Prompt Chain")

st.write("""
Test Planning is a critical phase in the Software Test Life Cycle (STLC), where the strategy, scope, resources, and schedule for testing are defined. This page facilitates the creation and management of your test plan using advanced techniques such as Chain of Thought (CoT) and Prompt Chain.

Upload the necessary files for the Test Planning process below:
""")

st.image("../images/test-planning.png", caption="Test Planning Process")

st.subheader("Why Do We Conduct Test Planning?")
st.write("""
- **Defining the Test Strategy**: Establishing the overall approach to testing, including test levels, types, and techniques to be used.
- **Determining the Test Scope**: Identifying the features and functionalities that need to be tested, as well as those that do not.
- **Resource and Schedule Planning**: Allocating resources, including team members, tools, and environments, and defining the testing timeline.
- **Risk Management**: Identifying potential risks and defining mitigation strategies to ensure a smooth testing process.
- **Ensuring Requirement Coverage**: Verifying that all specified requirements will be adequately tested.
""")

st.subheader("How Do We Conduct Test Planning?")
st.write("""
The Test Planning process typically involves the following steps:

1. **Document Review**: Reviewing requirements specification, technical design, use case diagrams, traceability matrix, and test cases to understand the project’s scope and objectives.
2. **Defining the Test Strategy**: Outlining the overall approach to testing, including what needs to be tested, how it will be tested, and the criteria for success.
3. **Resource Planning**: Identifying and assigning the necessary resources, such as personnel, tools, and environments required for testing.
4. **Risk Management**: Identifying potential risks in the testing process and planning how to mitigate them.
5. **Schedule Planning**: Establishing the timeline for testing activities, including key milestones and deadlines.
""")

st.subheader("Impact of Using Chain of Thought (CoT) and Prompt Chain in Test Planning")
st.write("""
Incorporating advanced techniques like Chain of Thought (CoT) and Prompt Chain into the Test Planning process can significantly enhance the thoroughness and effectiveness of the plan.

- **Chain of Thought (CoT)**: CoT enables a sequential reasoning approach, where the outcome of one planning stage feeds into the next. This method ensures that all aspects of the test plan, such as risk identification, resource allocation, and schedule planning, are considered in a logical sequence, leading to a more robust and comprehensive test plan.
  
- **Prompt Chain**: By using a series of prompts that guide the planning process, Prompt Chain structures ensure that the test plan is comprehensive and systematic. Each prompt is designed to focus on a specific aspect of test planning, ensuring that no critical detail is overlooked.

By combining these approaches, the Test Planning process becomes more robust, leading to a test plan that is better suited to ensure the quality and success of the software. The structured approach of CoT and Prompt Chains ensures that the plan is not only thorough but also adaptable to different testing scenarios and requirements.
""")

st.subheader("Start Test Planning with CoT and Prompt Chain")
st.write("""
The integration of advanced techniques like Chain of Thought (CoT) and Prompt Chain into the Test Planning process can significantly enhance the effectiveness and depth of the plan.

- **Python File**: The Python code file is a key component of the test planning process. CoT enables a sequential reasoning approach, where the insights gained from code analysis help shape the test strategy and scope. This approach ensures that the code is tested comprehensively, covering aspects such as functionality, performance, and security.
""")
uploaded_code_file = st.file_uploader("Upload your Python code file (.py)", type="py")

st.write("""
- **Technical Design Document**: The Technical Design Document provides the architectural blueprint of the software. By analyzing this document, the Prompt Chain structures help ensure that the test plan covers all critical design aspects, such as scalability, modularity, and adherence to design principles.
""")
uploaded_tech_design_file = st.file_uploader("Upload your Technical Design Document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

st.write("""
- **Requirements Specification Document**: The Requirements Specification Document outlines the functional and non-functional requirements of the software. In the Test Planning process, this document is essential for defining the test scope and ensuring that all requirements are covered in the test plan.
""")
uploaded_req_spec_file = st.file_uploader("Upload your Requirements Specification Document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

st.write("""
- **Use Case Diagrams and Stories**: These documents help to understand how the software is intended to be used. By analyzing these diagrams and stories, the Prompt Chain structures ensure that the test plan includes all user scenarios and that the software is tested in real-world conditions.
""")
uploaded_use_case_file = st.file_uploader("Upload your Use Case Document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

st.write("""
- **Traceability Matrix**: The Traceability Matrix is a crucial tool for tracking requirements throughout the development lifecycle. By cross-referencing the matrix with the source code, technical design, and requirements specification, the Prompt Chain structures help ensure that all requirements are fully tested. This step ensures that no requirement is overlooked, and the software is aligned with the initial project goals.
""")
uploaded_trace_matrix_file = st.file_uploader("Upload your Traceability Matrix (.pdf, .docx, .txt, .xlsx)", type=["pdf", "docx", "txt", "xlsx"])

st.write("""
- **Test Cases Document**: The Test Cases Document provides detailed scenarios and expected outcomes for testing the software. By analyzing the test cases, the Prompt Chain structures ensure that the test plan covers all scenarios and that the software meets the specified requirements.
""")
uploaded_test_cases_file = st.file_uploader("Upload your Test Cases Document (.xlsx)", type=["pdf", "docx", "txt", "xlsx"])

st.write("""
By combining these approaches, the Test Planning process becomes more robust, leading to a comprehensive test plan that is better suited to ensure the quality and success of the software. The structured approach of CoT and Prompt Chains ensures that the plan is not only thorough but also adaptable to different testing scenarios and requirements.
""")


# Function to review code using a specific model with retry and timeout
def review_code_with_model(model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, prompt_template, feedback="", retries=3, timeout=60):
    try:
        review_prompt = prompt_template.format(feedback=feedback, source_code=source_code, tech_design=tech_design, req_spec=req_spec, use_case=use_case, trace_matrix=trace_matrix, test_cases=test_cases)
        review_prompt += feedback
    except KeyError as e:
        st.error(f"An error occurred: Missing key in template - {e}")
        return "", ""

    for i in range(retries):
        try:
            review_output = model.invoke(review_prompt, timeout=timeout)
            return review_prompt, review_output
        except (ConnectionError, Timeout) as e:
            if i == retries - 1:
                st.error(f"An error occurred: {e}")
                return review_prompt, f"An error occurred: {e}"
            st.warning(f"Retrying... ({i + 1}/{retries})")

# Function to draw chat-like bubbles
def draw_bubble(text, position='left'):
    bubble_style = 'round,pad=0.3'
    boxprops = dict(boxstyle=bubble_style, facecolor='lightblue' if position == 'left' else 'lightgreen', alpha=0.5)
    st.write(f"<div style='border:1px solid black; padding:10px; margin:10px; border-radius:15px; width:auto; display:inline-block; max-width:80%; background-color:{'lightblue' if position == 'left' else 'lightgreen'}'><strong>{text}</strong></div>", unsafe_allow_html=True)

# Check if all files have been uploaded before proceeding
if (uploaded_code_file is not None and 
    uploaded_tech_design_file is not None and 
    uploaded_req_spec_file is not None and 
    uploaded_use_case_file is not None and 
    uploaded_trace_matrix_file is not None and
    uploaded_test_cases_file is not None):

    # Read the uploaded files
    source_code = uploaded_code_file.read().decode('utf-8')
    tech_design = uploaded_tech_design_file.read().decode('utf-8')
    req_spec = uploaded_req_spec_file.read().decode('utf-8')
    use_case = uploaded_use_case_file.read().decode('utf-8')
    if uploaded_trace_matrix_file.name.endswith('.xlsx'):
        # Read the Excel file
        trace_matrix = pd.read_excel(uploaded_trace_matrix_file)
    else:
        # Handle other file types (PDF, DOCX, TXT)
        trace_matrix = uploaded_trace_matrix_file.read().decode('utf-8')
    if uploaded_test_cases_file.name.endswith('.xlsx'):
        # Read the Excel file
        test_cases = pd.read_excel(uploaded_test_cases_file)
    else:
        # Handle other file types (PDF, DOCX, TXT)
        test_cases = uploaded_test_cases_file.read().decode('utf-8')

    if (len(source_code) <= 10000 and 
        len(tech_design) <= 10000 and 
        len(req_spec) <= 10000 and 
        len(use_case) <= 10000 and 
        len(trace_matrix) <= 10000 and
        len(test_cases) <= 10000):
        
        st.write("### Uploaded Files")
        st.write("#### Python Code")
        st.code(source_code, language='python')
        st.write("#### Technical Design Document")
        st.code(tech_design, language='plaintext')
        st.write("#### Requirements Specification Document")
        st.code(req_spec, language='plaintext')
        st.write("#### Use Case Document")
        st.code(use_case, language='plaintext')
        st.write("#### Traceability Matrix")
        st.dataframe(trace_matrix)
        st.write("#### Test Cases Document")
        st.dataframe(test_cases)

        use_cot = st.checkbox("Use Chain of Thought (CoT) & Prompt Chain Structure", value=True)
        if use_cot:
            if st.button("Get Suggestion by LLaMa 3.1 Model"):
                suggestion_model = models["llama3.1"]
                feedback = """
                
                MAIN PROMPT:
                Please pay attention: The only and main mission is creating test plan with duration times!
                Give me a JSON file at the end of the suggestion process as whole. Just create a JSON file which includes all the suggestions as a whole.
                Provide a Chain of Thought and Prompt Chain structure suggestion for this CREATING TEST PLAN process. CoT and Prompt Chain structures are parallel from top to bottom. For example: The output of LLM1 (left) will be the input of LLM3 (left) and the output of LLM2 (right) will be the input of LLM4 (right). The input of one LLM will be the input of the other and it is aimed to improve its weak aspects by evaluating it. There are 2 lines as left and right sides at each level. These left and right nodes represent a LLM. Models that can be used for CoT and Prompt Chain structures are: deepseek-coder, mathstral, codegemma, codellama and llama3.1 model. The models will be used at different levels with specific prompts for creating and then evaluating test plans, forming a strong Chain of Thought and Prompt Chain structure. Provide separate LLM proposals for the left and right nodes at each level and give suggestions on this subject also, give a JSON format for this purpose as an output! JSON format must be like a JSON as a whole! Just give one JSON structure as an output not multiple JSON structures. 
                Prompts must have the structure as "Create a test plan using the information of the files. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}, Trace Matrix: {trace_matrix}, Test Cases: {test_cases}, Feedback: {feedback}"
                All prompts' purpose are to create a test plan! Example of a prompt: "The only mission is "Creating Test Plan using information taking from other documents like python code, requirements, etc.Create a test plan (must) as a table (including rows and columns) that shows the tasks and the time it will take to complete them based on the provided source code, technical design document, requirement specification, use case, traceability matrix and test cases. If there is feedback, apply corrections to the blank and required parts in the test plan based on this feedback. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Trace Matrix: {trace_matrix}. Test Cases: {test_cases}"
                You must generate applicable prompts to use the models in the CoT and Prompt Chain structure.
                Give me a JSON file at the end of the suggestion process as whole.
                Expected JSON Format:
                {{
                    "suggestions": [
                        {{
                        "level": "<Level>",
                        "left_node": {{
                            "llm_model": "<LLM Model Name> (e.g., codegemma)",
                            "prompt": "<Suggestion for Left Node> (Example: The mission is "Creating Test Plan using information taking from other documents like python code, requirements, etc. (e.g., Create a test plan (must) as a table (including rows and columns) that shows the tasks and the time it will take to complete them based on the provided source code, technical design document, requirement specification, use case, traceability matrix and test cases. If there is feedback, apply corrections to the blank and required parts in the test plan based on this feedback. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Trace Matrix: {trace_matrix}. Test Cases: {test_cases},")
                        "right_node": {{
                            "llm_model": "<LLM Model Name> (e.g., codellama)",
                            "prompt": "<Suggestion for Right Node> (Example: The mission is "Creating Test Plan using information taking from other documents like python code, requirements, etc. (e.g., Create a test plan (must) as a table (including rows and columns) that shows the tasks and the time it will take to complete them based on the provided source code, technical design document, requirement specification, use case, traceability matrix and test cases. If there is feedback, apply corrections to the blank and required parts in the test plan based on this feedback. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Use Case: {use_case}. Trace Matrix: {trace_matrix}. Test Cases: {test_cases}")
                        }}
                        }},
                        # Add as many levels as necessary
                    ]
                }}

                """

                # Create the suggestion prompt using the combined inputs
                suggestion_prompt = default_prompts["llama3.1"].format(
                    source_code=source_code,
                    tech_design=tech_design,
                    req_spec=req_spec,
                    use_case=use_case,
                    trace_matrix=trace_matrix,
                    test_cases=test_cases,
                    feedback= feedback
                )
    
                # Call the review function with the suggestion model and prompt
                _, st.session_state.suggestion_output = review_code_with_model(suggestion_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, feedback, suggestion_prompt)
    
            # Display suggestion if available
            if st.session_state.suggestion_output:
                st.write("### Suggested Chain of Thought (CoT) & Prompt Chain Structure")
                st.write(st.session_state.suggestion_output)
                if st.button("Apply the Suggested Structure"):
                    st.session_state.apply_suggestion = True
                    suggested_json_structure = extract_and_save_json(st.session_state.suggestion_output, "test_plan_suggested_structure.json")

            if st.button("Configure Models and Prompts"):
                st.session_state.configure_models = True

            if st.session_state.apply_suggestion:
                try:
                    with open('test_plan_suggested_structure.json', 'r') as suggested_json_file:
                        suggestions_data = json.load(suggested_json_file)

                    selected_models = []
                    custom_prompts = []

                    for suggestion in suggestions_data.get("suggestions", []):
                        try:
                            left_model = suggestion["left_node"].get("llm_model", None)
                            right_model = suggestion["right_node"].get("llm_model", None)
                            selected_models.append((left_model, right_model))

                            left_prompt = suggestion["left_node"].get("prompt", None)
                            right_prompt = suggestion["right_node"].get("prompt", None)

                            custom_prompts.append((left_prompt, right_prompt))
                        
                        except KeyError as e:
                            st.warning(f"Missing key in suggestion: {e}")
                            continue

                    st.write("Selected Models:", selected_models)
                    st.write("Custom Prompts:", custom_prompts)

                except FileNotFoundError:
                    st.error("The file 'test_plan_suggested_structure.json' was not found.")
                except json.JSONDecodeError:
                    st.error("Failed to decode JSON from 'test_plan_suggested_structure.json'.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

                previous_feedback = ""
                for i, (model_keys, prompts) in enumerate(zip(selected_models, custom_prompts)):
                    left_model_key, right_model_key = model_keys
                    left_prompt, right_prompt = prompts
                    left_model = models.get(left_model_key)
                    right_model = models.get(right_model_key)

                    if left_model is None or right_model is None:
                        st.error(f"Model for key {left_model_key} or {right_model_key} not found.")
                        continue

                    st.write(f"### Level {i + 1}")

                    # Review with left model
                    left_prompt_text, left_feedback = review_code_with_model(left_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, left_prompt, previous_feedback)
                    draw_bubble(f"Output:\n {left_feedback}", position='left')

                    # Review with right model
                    right_prompt_text, right_feedback = review_code_with_model(right_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, right_prompt, previous_feedback)
                    draw_bubble(f"Output:\n {right_feedback}", position='right')

                    # Combine feedback from both models
                    previous_feedback = f"Left Model Feedback: {left_feedback}\nRight Model Feedback: {right_feedback}"

                    # Store outputs
                    st.session_state.outputs.append({
                        "level": i + 1,
                        "left_model": left_model_key,
                        "left_prompt": left_prompt_text,
                        "left_output": left_feedback,
                        "right_model": right_model_key,
                        "right_prompt": right_prompt_text,
                        "right_output": right_feedback
                    })

                # Final evaluation with LLaMa 3.1 model instead of RAG model
                final_model_key = "llama3.1"
                final_model = models[final_model_key]
                if final_model:
                    st.write("### Final Evaluation by LLaMa 3.1 Model")
                    final_prompt_text, final_output = review_code_with_model(final_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, default_prompts[final_model_key], previous_feedback)
                    st.write(final_output)

                    # Store final output
                    st.session_state.outputs.append({
                        "final_model": final_model_key,
                        "final_prompt": final_prompt_text,
                        "final_output": final_output
                    })

                # Mark review as completed
                st.session_state.review_completed = True

        if st.session_state.configure_models:
            st.write("### Settings of Chain of Thought (CoT) & Prompt Chain Structure")

            # Maximum number of levels
            st.session_state.max_levels = st.number_input("Enter maximum number of CoT levels", min_value=2, step=1, format="%d", value=st.session_state.max_levels)

            # CoT depth
            st.session_state.depth = st.slider(f"CoT Depth (Number of Levels, max {st.session_state.max_levels})", min_value=1, max_value=st.session_state.max_levels, value=st.session_state.depth)

            # List to store selected models and prompts for each level
            selected_models = []
            custom_prompts = []

            for i in range(st.session_state.depth):
                # Selection of two LLM models per level
                left_model_key = st.selectbox(f"Left LLM Model (Level {i + 1})", list(model_options.values()), format_func=lambda x: x, key=f"left_model_{i}")
                right_model_key = st.selectbox(f"Right LLM Model (Level {i + 1})", list(model_options.values()), format_func=lambda x: x, key=f"right_model_{i}")

                selected_models.append((left_model_key, right_model_key))

                # Prompt customization options
                left_default_prompt = default_prompts[left_model_key]
                right_default_prompt = default_prompts[right_model_key]

                # Left model custom prompt
                if f"left_prompt_{i}" not in st.session_state.custom_prompts:
                    st.session_state.custom_prompts[f"left_prompt_{i}"] = left_default_prompt

                use_custom_left_prompt = st.checkbox(f"Customize Left Model Prompt", key=f"custom_left_check_{i}")
                if use_custom_left_prompt:
                    left_prompt = st.text_area(f"Enter Custom Prompt for {left_model_key}", value=st.session_state.custom_prompts[f"left_prompt_{i}"], key=f"left_prompt_{i}")
                    st.session_state.custom_prompts[f"left_prompt_{i}"] = left_prompt
                else:
                    left_prompt = left_default_prompt

                # Right model custom prompt
                if f"right_prompt_{i}" not in st.session_state.custom_prompts:
                    st.session_state.custom_prompts[f"right_prompt_{i}"] = right_default_prompt

                use_custom_right_prompt = st.checkbox(f"Customize Right Model Prompt", key=f"custom_right_check_{i}")
                if use_custom_right_prompt:
                    right_prompt = st.text_area(f"Enter Custom Prompt for {right_model_key}", value=st.session_state.custom_prompts[f"right_prompt_{i}"], key=f"right_prompt_{i}")
                    st.session_state.custom_prompts[f"right_prompt_{i}"] = right_prompt
                else:
                    right_prompt = right_default_prompt

                custom_prompts.append((left_prompt, right_prompt))

        else:
            # Use LLaMa 3.1 model if CoT is not used
            selected_models = [("llama3.1", "llama3.1")]
            custom_prompts = [(default_prompts["llama3.1"], default_prompts["llama3.1"])]

        # Start button
        if st.button("Start Application"):
            st.write("Configuring models based on your selections...")

            previous_feedback = ""
            for i, (model_keys, prompts) in enumerate(zip(selected_models, custom_prompts)):
                left_model_key, right_model_key = model_keys
                left_prompt, right_prompt = prompts
                left_model = models.get(left_model_key)
                right_model = models.get(right_model_key)

                if left_model is None or right_model is None:
                    st.error(f"Model for key {left_model_key} or {right_model_key} not found.")
                    continue

                st.write(f"### Level {i + 1}")

                # Review with left model
                left_prompt_text, left_feedback = review_code_with_model(left_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, left_prompt, previous_feedback)
                draw_bubble(f"Output:\n {left_feedback}", position='left')

                # Review with right model
                right_prompt_text, right_feedback = review_code_with_model(right_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, right_prompt, previous_feedback)
                draw_bubble(f"Output:\n {right_feedback}", position='right')

                # Combine feedback from both models
                previous_feedback = f"Left Model Feedback: {left_feedback}\nRight Model Feedback: {right_feedback}"

                # Store outputs
                st.session_state.outputs.append({
                    "level": i + 1,
                    "left_model": left_model_key,
                    "left_prompt": left_prompt_text,
                    "left_output": left_feedback,
                    "right_model": right_model_key,
                    "right_prompt": right_prompt_text,
                    "right_output": right_feedback
                })

            # Final evaluation with LLaMa 3.1 model instead of RAG model
            final_model_key = "llama3.1"
            final_model = models[final_model_key]
            if final_model:
                st.write("### Final Evaluation by LLaMa 3.1 Model")
                final_prompt_text, final_output = review_code_with_model(final_model, source_code, tech_design, req_spec, use_case, trace_matrix, test_cases, default_prompts[final_model_key], previous_feedback)
                st.write(final_output)

                # Store final output
                st.session_state.outputs.append({
                    "final_model": final_model_key,
                    "final_prompt": final_prompt_text,
                    "final_output": final_output
                })

            # Mark review as completed
            st.session_state.review_completed = True

        if st.session_state.review_completed:
            # Save buttons for all levels
            for i in range(st.session_state.depth):
                if st.button(f"Save Outputs to txt (Level {i + 1})", key=f"save_txt_level_{i}"):
                    st.session_state.level_output_saved[f"level_{i}_txt"] = True
                    txt_filename = f"code_review_outputs_level_{i + 1}.txt"
                    with open(txt_filename, 'w') as txt_file:
                        for key, value in st.session_state.outputs[i].items():
                            txt_file.write(f"{key}: {value}\n")
                        txt_file.write("\n")
                    st.write(f"Outputs for Level {i + 1} saved to {txt_filename}")

                if st.button(f"Save Outputs to JSON (Level {i + 1})", key=f"save_json_level_{i}"):
                    st.session_state.level_output_saved[f"level_{i}_json"] = True
                    json_filename = f"code_review_outputs_level_{i + 1}.json"
                    with open(json_filename, 'w') as json_file:
                        json.dump(st.session_state.outputs[i], json_file, indent=4)
                    st.write(f"Outputs for Level {i + 1} saved to {json_filename}")

                if f"level_{i}_txt" in st.session_state.level_output_saved:
                    st.success(f"Outputs for Level {i + 1} saved to txt.")
                if f"level_{i}_json" in st.session_state.level_output_saved:
                    st.success(f"Outputs for Level {i + 1} saved to JSON.")

            # Save buttons for final evaluation
            if st.button("Save Final Outputs to txt"):
                st.session_state.final_output_saved = True
                txt_filename = "final_code_review_outputs.txt"
                with open(txt_filename, 'w') as txt_file:
                    for output in st.session_state.outputs:
                        for key, value in output.items():
                            txt_file.write(f"{key}: {value}\n")
                        txt_file.write("\n")
                st.write(f"Final outputs saved to {txt_filename}")

            if st.button("Save Final Outputs to JSON"):
                st.session_state.final_output_saved = True
                json_filename = "final_code_review_outputs.json"
                with open(json_filename, 'w') as json_file:
                    json.dump(st.session_state.outputs, json_file, indent=4)
                st.write(f"Final outputs saved to {json_filename}")

            if st.session_state.final_output_saved:
                st.success("Final outputs have been saved.")
    else:
        st.warning("Please upload files with a total size of less than 10.000 characters each.")

else:
    st.warning("Please upload all the required files (Python code, Technical Design Document, Requirements Specification Document, Use Case Document, and Traceability Matrix) to proceed.")
