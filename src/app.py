import streamlit as st
from streamlit_option_menu import option_menu
import os
import importlib.util

# Function to load and execute a script dynamically
def load_script(file_path):
    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

# Function to display the home page
def display_home_page():
    st.title("Software Test Lifecycle (STLC)")
    st.write("""
    Welcome to the Software Test Lifecycle (STLC) management application. This platform guides you through various 
    stages of the STLC process, ensuring comprehensive and systematic testing of your software applications. 
    Each stage is meticulously designed to enhance the quality, efficiency, and reliability of your software.
    """)
    
    st.write("### STLC Phases Overview")
    st.write("""
    1. **Requirement Analysis**: Identifying and understanding the testing requirements from the provided documents.
    2. **Test Planning**: Defining the strategy, objectives, resources, and schedule for the testing activities.
    3. **Test Scenario Generation**: Creating detailed test scenarios based on the requirements and design documents.
    4. **Test Scenario Optimization**: Enhancing the test scenarios for maximum coverage and efficiency.
    5. **Test Code Generation**: Converting test scenarios into executable test scripts.
    6. **Environment Setup**: Preparing the hardware and software environment necessary for testing.
    7. **Test Execution**: Running the tests and recording the outcomes.
    8. **Test Reporting**: Documenting the results, observations, and findings from the test execution.
    9. **Test Closure**: Concluding the testing process with a final evaluation and report.
    """)
    
    st.write("### STLC Process Diagram")
    st.image("stlc_diagram.jpg", caption="Software Test Lifecycle (STLC) Diagram")

    st.title("Code Review")
    st.write("""
    ### Code Review: Elevating Code Quality to the Next Level
    
    Code review is a critical phase in the software development lifecycle, ensuring that code is scrutinized for 
    potential issues, adherence to coding standards, and overall quality. By incorporating code reviews into your 
    workflow, you achieve multiple benefits:
    
    - **Improved Code Quality**: Identifies bugs, vulnerabilities, and logical errors before they reach production.
    - **Knowledge Sharing**: Promotes a collaborative environment where team members can learn from each other.
    - **Consistency**: Ensures adherence to coding standards and best practices across the codebase.
    - **Efficiency**: Reduces technical debt and future rework by catching issues early.
    - **Accountability**: Fosters a culture of accountability and pride in code ownership.
    
    Our platform provides a robust code review module that integrates seamlessly with your development process, 
    leveraging advanced AI models like CodeGemma, CodeLLaMa, and LLaMa3 to assist in the review process. 
    This ensures not only accuracy but also comprehensive coverage of potential issues.
    
    Embrace the power of code reviews to elevate the quality of your software and foster a culture of continuous improvement.
    """)

# Create a sidebar menu
with st.sidebar:
    selected_option = option_menu(
        "Test Management Menu",
        [
            "Home",
            "1. Code Review",
            "2. Requirement Analysis",
            "3. Test Planning",
            "4. Test Scenario Generation",
            "5. Test Scenario Optimization",
            "6. Test Code Generation",
            "7. Environment Setup",
            "8. Test Execution",
            "9. Test Reporting",
            "10. Test Closure"
        ],
        icons=["house", "code", "file-text", "calendar", "list", "file-text", "terminal", "tools", "play", "bar-chart", "check-square"],
        menu_icon="cast",
        default_index=0,
    )

# Dictionary mapping menu options to file paths
file_paths = {
    "1. Code Review": "1_code_review.py",
    "2. Requirement Analysis": "2_req_analysis.py",
    "3. Test Planning": "3_test_planning.py",
    "4. Test Scenario Generation": "4_test_scenario_generation.py",
    "5. Test Scenario Optimization": "5_test_scenario_optimization.py",
    "6. Test Code Generation": "6_test_code_generation.py",
    "7. Environment Setup": "7_environment_setup.py",
    "8. Test Execution": "8_test_execution.py",
    "9. Test Reporting": "9_test_reporting.py",
    "10. Test Closure": "10_test_closure.py"
}

# Load the selected script or display the home page
if selected_option == "Home":
    display_home_page()
elif selected_option in file_paths:
    file_path = file_paths[selected_option]
    if os.path.exists(file_path):
        load_script(file_path)
    else:
        st.error(f"The file {file_path} does not exist.")
else:
    st.error("Please select a valid option.")
