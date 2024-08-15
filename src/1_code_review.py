import streamlit as st
import json
from langchain_community.llms import Ollama
from requests.exceptions import ConnectionError, Timeout
from src.json_extractor import extract_and_save_json

# Define the default prompts directly in the script
default_prompts = {
    "deepseek-coder": "Based on the following feedback, source code, technical design document, and requirements specification, identify potential security vulnerabilities, performance issues, and adherence to best coding practices. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Feedback: {feedback}",
    "codegemma": "Following the previous review, analyze the code snippet for quality, performance, and adherence to best practices, considering the technical design and requirements specification. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Prior Feedback: {feedback}. Focus on readability, maintainability, and efficiency.",
    "codellama": "Building on prior feedback, review the code for improvements in performance, security, and maintainability, taking into account the technical design and requirements specification. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Previous Feedback: {feedback}. Provide detailed recommendations.",
    "llama3.1": "Evaluate the overall quality and potential issues in the code based on all prior reviews, along with the technical design and requirements specification. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Cumulative Feedback: {feedback}. Summarize strengths, weaknesses, and suggest improvements.",
    "mathstral": "Review the code for mathematical or logical errors, ensuring formulas and numerical methods are correct and efficient, considering the technical design and requirements specification. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Previous Feedback: {feedback}. Suggest enhancements for accuracy and performance."
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
if "apply_suggestion" not in st.session_state:
    st.session_state.apply_suggestion = False
if "final_output_saved" not in st.session_state:
    st.session_state.final_output_saved = False
if "review_completed" not in st.session_state:
    st.session_state.review_completed = False
if "level_output_saved" not in st.session_state:
    st.session_state.level_output_saved = {}

# Title and Introduction
st.title("Code Review Process with Chain of Thought (CoT) and Prompt Chain")

st.write("""
Code Review is an essential part of the software development process, aimed at improving the quality, maintainability, and security of the codebase. Through systematic examination of the code by peers or automated tools, potential issues can be identified early, ensuring that the software meets the required standards before it is integrated into the main codebase.
""")
st.image("../images/code_review.png", caption="Code Review Process")

st.subheader("Why Do We Conduct Code Reviews?")
st.write("""
- **Early Detection of Issues**: Identifying bugs, performance bottlenecks, and security vulnerabilities before they affect production.
- **Improving Code Quality**: Enhancing readability, maintainability, and adherence to coding standards and best practices.
- **Facilitating Knowledge Sharing**: Promoting collaboration among team members and spreading knowledge about the codebase.
- **Ensuring Compliance**: Making sure that the code follows the required guidelines and industry standards, such as security and data protection regulations.
""")

st.subheader("How Do We Conduct Code Reviews?")
st.write("""
The Code Review process is typically structured as follows:

1. **Preparation**: The developer prepares the code for review by ensuring it meets the basic standards and is ready for feedback.
2. **Review**: The code is examined by one or more reviewers who look for issues such as bugs, inefficiencies, and violations of coding standards.
3. **Feedback**: The reviewers provide constructive feedback, highlighting areas for improvement or refactoring.
4. **Revision**: The developer addresses the feedback by making the necessary changes and resubmitting the code.
5. **Approval**: Once the code passes the review and all concerns are addressed, it is approved and merged into the main codebase.
""")

st.subheader("Impact of Using Chain of Thought (CoT) and Prompt Chain in Code Review")
st.write("""
The integration of advanced techniques like Chain of Thought (CoT) and Prompt Chain into the Code Review process can significantly enhance the effectiveness and depth of the review.

- **Chain of Thought (CoT)**: CoT enables a sequential reasoning approach, where the output of one model becomes the input for another. This allows for a more thorough examination of the code, as different aspects (e.g., security, performance, maintainability) are considered in a logical sequence. By simulating a human-like thought process, CoT can help in identifying complex issues that might be overlooked in a standard review.

- **Prompt Chain**: By using a series of prompts that guide the review process, Prompt Chain structures can ensure that the review is comprehensive and systematic. Each prompt is designed to focus on a specific aspect of the code, ensuring that no important detail is missed. This method helps in organizing the review process, making it more efficient and effective.

By combining these approaches, the Code Review process becomes more robust, leading to higher-quality software that is better suited to meet the demands of modern applications. The structured approach of CoT and Prompt Chains ensures that the review is not only thorough but also adaptable to different scenarios and requirements.
""")

st.image("chain_of_thought.jpg", caption="Benefits of Prompt Chaining")

st.subheader("Start Code Review Process with CoT and Prompt Chain")
st.write("""
The integration of advanced techniques like Chain of Thought (CoT) and Prompt Chain into the Code Review process can significantly enhance the effectiveness and depth of the review.

- **Python File**: The Python code file is at the core of the review process. CoT enables a sequential reasoning approach, where the output of one model becomes the input for another. This approach allows for a more thorough examination of the code, addressing various aspects such as security, performance, and maintainability in a logical sequence. By simulating a human-like thought process, CoT helps in identifying complex issues that might be overlooked in a standard review, especially within the code logic and structure.
""")
uploaded_code_file = st.file_uploader("Upload your Python code file (.py)", type="py")

st.write("""
- **Technical Design Document**: The Technical Design Document provides the architectural blueprint of the software. By using a series of prompts that guide the review process, Prompt Chain structures ensure that the design is evaluated comprehensively and systematically. Each prompt is designed to focus on specific aspects of the architecture, such as scalability, modularity, and adherence to design principles. This method organizes the review process, making it more efficient and effective, and ensures that the design aligns with the intended software functionality.
""")
uploaded_tech_design_file = st.file_uploader("Upload your Technical Design Document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

st.write("""
- **Requirements Specification Document**: The Requirements Specification Document outlines the functional and non-functional requirements of the software. In the Code Review process, this document is essential for verifying that the code and design meet the specified requirements. Prompt Chains help ensure that each requirement is thoroughly reviewed, cross-referencing the code and design to confirm compliance. This step is crucial for validating that the final product fulfills the business and technical needs as outlined in the requirements.
""")
uploaded_req_spec_file = st.file_uploader("Upload your Requirements Specification Document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

st.write("""
By combining these approaches, the Code Review process becomes more robust, leading to higher-quality software that is better suited to meet the demands of modern applications. The structured approach of CoT and Prompt Chains ensures that the review is not only thorough but also adaptable to different scenarios and requirements.
""")


# Function to review code using a specific model with retry and timeout
def review_code_with_model(model, source_code, tech_design, req_spec, prompt_template, feedback="", retries=3, timeout=60):
    try:
        review_prompt = prompt_template.format(source_code=source_code, tech_design=tech_design, req_spec=req_spec, feedback=feedback)
        review_prompt += """Please pay attention: The only and main mission is creating test plan with duration times!"""
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

# Check if files have been uploaded before proceeding
if uploaded_code_file is not None and uploaded_tech_design_file is not None and uploaded_req_spec_file is not None:
    # Read the uploaded files
    source_code = uploaded_code_file.read().decode('utf-8')
    tech_design = uploaded_tech_design_file.read().decode('utf-8')
    req_spec = uploaded_req_spec_file.read().decode('utf-8')
    
    if len(source_code) <= 15000 and len(tech_design) <= 15000 and len(req_spec) <= 15000:
        st.write("### Uploaded Files")
        st.write("#### Python Code")
        st.code(source_code, language='python')
        st.write("#### Technical Design Document")
        st.code(tech_design, language='plaintext')
        st.write("#### Requirements Specification Document")
        st.code(req_spec, language='plaintext')
        use_cot = st.checkbox("Use Chain of Thought (CoT) & Prompt Chain Structure", value=True)
        if use_cot:
            if st.button("Get Suggestion by LLaMa 3.1 Model"):    
                suggestion_model = models["llama3.1"]
                feedback = """
                Provide a Chain of Thought and Prompt Chain structure suggestion for this code review process. CoT and Prompt Chain structures are parallel from top to bottom. For example: The output of LLM1 (left) will be the input of LLM3 (left) and the output of LLM2 (right) will be the input of LLM4 (right). The input of one LLM will be the input of the other and it is aimed to improve its weak aspects by evaluating it. There are 2 lines as left and right sides at each level. These left and right nodes represent a LLM. Models that can be used for CoT and Prompt Chain structures are: deepseek-coder, mathstral, codegemma, codellama and llama3.1 model. The models will be used at different levels with specific prompts, forming a strong Chain of Thought and Prompt Chain structure. Provide separate LLM proposals for the left and right nodes at each level and give suggestions on this subject also, give a JSON format for this purpose as an output! JSON format must be like a JSON as a whole! Just give one JSON structure as an output not multiple JSON structures. You should follow the expected JSON format strictly.
                Prompts must have the structure as "The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Feedback: {feedback}"
                Example of a prompt: "Based on the following feedback, source code, technical design document, and requirements specification, identify potential security vulnerabilities, performance issues, and adherence to best coding practices. The source code is: {source_code}. Technical Design: {tech_design}. Requirements Specification: {req_spec}. Feedback: {feedback}"
                You must generate applicable prompts to use the models in the CoT and Prompt Chain structure.
                Expected JSON Format:
                {{
                    "suggestions": [
                        {{
                        "level": "<Level>",
                        "left_node": {{
                            "llm_model": "<LLM Model Name>",
                            "prompt": "<Suggestion for Left Node>"
                        }},
                        "right_node": {{
                            "llm_model": "<LLM Model Name>",
                            "prompt": "<Suggestion for Right Node>"
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
                    feedback= feedback
                )
    
                # Call the review function with the suggestion model and prompt
                _, st.session_state.suggestion_output = review_code_with_model(suggestion_model, source_code, tech_design, req_spec, feedback, suggestion_prompt)
    

            
            # Display suggestion if available
            if st.session_state.suggestion_output:
                st.write("### Suggested Chain of Thought (CoT) & Prompt Chain Structure")
                st.write(st.session_state.suggestion_output)
                if st.button("Apply the Suggested Structure"):
                    st.session_state.apply_suggestion = True
                    suggested_json_structure = extract_and_save_json(st.session_state.suggestion_output, "suggested_structure.json")

            
            if st.button("Configure Models and Prompts"):
                st.session_state.configure_models = True            

            if st.session_state.apply_suggestion:
                try:
                    with open('suggested_structure.json', 'r') as suggested_json_file:
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
                    st.error("The file 'suggested_structure.json' was not found.")
                except json.JSONDecodeError:
                    st.error("Failed to decode JSON from 'suggested_structure.json'.")
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
                    left_prompt_text, left_feedback = review_code_with_model(left_model, source_code, tech_design, req_spec, left_prompt, previous_feedback)
                    draw_bubble(f"Output:\n {left_feedback}", position='left')
                    
                    # Review with right model
                    right_prompt_text, right_feedback = review_code_with_model(right_model, source_code, tech_design, req_spec, right_prompt, previous_feedback)
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
                    final_prompt_text, final_output = review_code_with_model(final_model, source_code, tech_design, req_spec, default_prompts[final_model_key], previous_feedback)
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
                left_prompt_text, left_feedback = review_code_with_model(left_model, source_code, tech_design, req_spec, left_prompt, previous_feedback)
                draw_bubble(f"Output:\n {left_feedback}", position='left')
                
                # Review with right model
                right_prompt_text, right_feedback = review_code_with_model(right_model, source_code, tech_design, req_spec, right_prompt, previous_feedback)
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
                final_prompt_text, final_output = review_code_with_model(final_model, source_code, tech_design, req_spec, default_prompts[final_model_key], previous_feedback)
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
        st.warning("Please upload files with a total size of less than 15.000 characters each.")  

else:
    st.warning("Please upload all the required files (Python code, Technical Design Document, and Requirements Specification Document) to proceed.")
