import streamlit as st
import json
import pickle
import os
from langchain_community.llms import Ollama
from requests.exceptions import ConnectionError, Timeout
import subprocess

# Define the default prompts directly in the script
default_prompts = {
    "deepseek-coder": "Based on the following inputs, execute the provided test scenarios and code. Inputs are: {input_content}. Record, analyze, and report the test results, including any errors or failures observed.",
    "codegemma": "Analyze the given inputs to execute the provided test scenarios and code. The inputs are: {input_content}. Focus on recording, analyzing, and reporting the test results, highlighting any errors or failures.",
    "codellama": "Review the inputs to execute the provided test scenarios and code. The inputs are: {input_content}. Provide detailed reports on the test results, including any errors or failures observed.",
    "llama3.1": "Evaluate the inputs to execute the provided test scenarios and code. The inputs are: {input_content}. Summarize the test results, analyze any errors or failures, and suggest improvements.",
    "mathstral": "Review the inputs to execute the provided test scenarios and code. The inputs are: {input_content}. Include detailed reports on the test results, highlight any errors or failures, and suggest improvements."
}

# Define the model options
model_options = {
    "DeepSeek Coder": "deepseek-coder",
    "CodeGemma": "codegemma",
    "CodeLLaMa": "codellama",
    "LLaMa 3.1": "llama3.1",
    "MathStral": "mathstral"
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
if "final_output_saved" not in st.session_state:
    st.session_state.final_output_saved = False
if "review_completed" not in st.session_state:
    st.session_state.review_completed = False
if "level_output_saved" not in st.session_state:
    st.session_state.level_output_saved = {}

# Title and description
st.title("Test Execution")
st.write("This application allows users to configure an LLM-based system for executing test scenarios and code, and recording the results using various models.")

# File upload for test execution
uploaded_file = st.file_uploader("Upload your Python test code file (.py)", type="py")

# Additional inputs for test execution
st.write("### Additional Inputs for Test Execution")
test_environment = st.text_area("Enter test environment and hardware/software configurations (if any):", "")
test_tools = st.text_area("Enter test tools and frameworks (if any):", "")
test_data = st.text_area("Enter test data and user inputs (if any):", "")

# Function to review inputs using a specific model with retry and timeout
def review_inputs_with_model(model, input_content, prompt_template, retries=3, timeout=60):
    review_prompt = prompt_template.format(input_content=input_content)
    for i in range(retries):
        try:
            review_output = model.invoke(review_prompt, timeout=timeout)
            return review_prompt, review_output
        except (ConnectionError, Timeout) as e:
            if i == retries - 1:
                return review_prompt, f"An error occurred: {e}"
            print(f"Retrying... ({i + 1}/{retries})")

# Function to execute the uploaded Python test code and capture the output
def execute_python_code(file_path):
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True, timeout=60)
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", "The code execution timed out."
    except Exception as e:
        return "", str(e)

# Function to draw chat-like bubbles
def draw_bubble(text, position='left'):
    bubble_style = 'round,pad=0.3'
    boxprops = dict(boxstyle=bubble_style, facecolor='lightblue' if position == 'left' else 'lightgreen', alpha=0.5)
    st.write(f"<div style='border:1px solid black; padding:10px; margin:10px; border-radius:15px; width:auto; display:inline-block; max-width:80%; background-color:{'lightblue' if position == 'left' else 'lightgreen'}'><strong>{text}</strong></div>", unsafe_allow_html=True)

# Check if a file has been uploaded before proceeding
if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    file_path = os.path.join("/tmp", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Read the uploaded file
    code_content = uploaded_file.read().decode('utf-8')
    if len(code_content) <= 15000:
        st.text_area("Uploaded Python Test Code", code_content, height=300)
        
        use_cot = st.checkbox("Use Chain of Thought (CoT) & Prompt Chain Structure", value=True)
        if use_cot:
            if st.button("Get Suggestion by LLaMa 3.1 Model"):    
                suggestion_model = models["llama3.1"]
                combined_inputs = f"Python Test Code: {code_content}\nTest Environment: {test_environment}\nTest Tools: {test_tools}\nTest Data: {test_data}"
                suggestion_prompt = default_prompts["llama3.1"].format(
                    input_content=combined_inputs
                )
                _, st.session_state.suggestion_output = review_inputs_with_model(suggestion_model, combined_inputs, suggestion_prompt)
            
            # Display suggestion if available
            if st.session_state.suggestion_output:
                st.write("### Suggested Chain of Thought (CoT) & Prompt Chain Structure")
                st.write(st.session_state.suggestion_output)
            
            if st.button("Configure Models and Prompts"):
                st.session_state.configure_models = True
        
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
            combined_inputs = f"Python Test Code: {code_content}\nTest Environment: {test_environment}\nTest Tools: {test_tools}\nTest Data: {test_data}"
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
                left_prompt_text, left_feedback = review_inputs_with_model(left_model, combined_inputs, left_prompt)
                draw_bubble(f"Output:\n {left_feedback}", position='left')
                
                # Review with right model
                right_prompt_text, right_feedback = review_inputs_with_model(right_model, combined_inputs, right_prompt)
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
                final_prompt_text, final_output = review_inputs_with_model(final_model, combined_inputs, default_prompts[final_model_key])
                st.write(final_output)

                # Store final output
                st.session_state.outputs.append({
                    "final_model": final_model_key,
                    "final_prompt": final_prompt_text,
                    "final_output": final_output
                })

            # Mark review as completed
            st.session_state.review_completed = True

            # Execute the uploaded Python test code and display the output
            if st.button("Execute Test Code"):
                stdout, stderr = execute_python_code(file_path)
                st.write("### Test Code Execution Output")
                if stdout:
                    st.write("**Standard Output:**")
                    st.code(stdout)
                if stderr:
                    st.write("**Error Output:**")
                    st.code(stderr)

        if st.session_state.review_completed:
            # Save buttons for all levels
            for i in range(st.session_state.depth):
                if st.button(f"Save Outputs to txt (Level {i + 1})", key=f"save_txt_level_{i}"):
                    st.session_state.level_output_saved[f"level_{i}_txt"] = True
                    txt_filename = f"test_execution_outputs_level_{i + 1}.txt"
                    with open(txt_filename, 'w') as txt_file:
                        for key, value in st.session_state.outputs[i].items():
                            txt_file.write(f"{key}: {value}\n")
                        txt_file.write("\n")
                    st.write(f"Outputs for Level {i + 1} saved to {txt_filename}")

                if st.button(f"Save Outputs to JSON (Level {i + 1})", key=f"save_json_level_{i}"):
                    st.session_state.level_output_saved[f"level_{i}_json"] = True
                    json_filename = f"test_execution_outputs_level_{i + 1}.json"
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
                txt_filename = "final_test_execution_outputs.txt"
                with open(txt_filename, 'w') as txt_file:
                    for output in st.session_state.outputs:
                        for key, value in output.items():
                            txt_file.write(f"{key}: {value}\n")
                        txt_file.write("\n")
                st.write(f"Final outputs saved to {txt_filename}")

            if st.button("Save Final Outputs to JSON"):
                st.session_state.final_output_saved = True
                json_filename = "final_test_execution_outputs.json"
                with open(json_filename, 'w') as json_file:
                    json.dump(st.session_state.outputs, json_file, indent=4)
                st.write(f"Final outputs saved to {json_filename}")

            if st.session_state.final_output_saved:
                st.success("Final outputs have been saved.")
    else:
        st.warning("The uploaded file exceeds the 15,000 character limit. Please upload a shorter file.")  

else:
    st.warning("Please upload a Python test code file to proceed.")
