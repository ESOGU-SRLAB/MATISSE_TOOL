import streamlit as st
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import uuid
from ollama import chat

# TestCase model
class TestCase(BaseModel):
    ScenarioID: str
    TestCaseID: str
    Title: str
    Description: Optional[str] = None
    Objective: Optional[str] = None

# TestCaseList model
class TestCaseList(BaseModel):
    test_cases: List[TestCase]
    comparison_logs: List[dict] = []
    duplicates: List[dict] = []  # Benzer test durumlarını saklamak için yeni bir liste

    def smart_select(self):
        unique_cases = []
        step = 1

        for case in self.test_cases:
            is_duplicate = False
            for unique_case in unique_cases:
                try:
                    comparison_result = self._query_llm_similarity(case, unique_case)
                except ValueError as e:
                    st.warning(f"LLM comparison failed: {e}")
                    comparison_result = False

                self.comparison_logs.append({
                    "Step": step,
                    "ProcessName": str(uuid.uuid4()),
                    "Timestamp": datetime.now().isoformat(),
                    "Case1": case.model_dump(),
                    "Case2": unique_case.model_dump(),
                    "is_same": comparison_result,
                })
                step += 1
                if comparison_result:
                    is_duplicate = True
                    # Benzer test durumlarını kaydet
                    self.duplicates.append({
                        "DuplicateCase": case.model_dump(),
                        "MatchedWith": unique_case.model_dump()
                    })
                    break

            if not is_duplicate:
                unique_cases.append(case)

        return TestCaseList(
            test_cases=unique_cases,
            comparison_logs=self.comparison_logs,
            duplicates=self.duplicates
        )

    @staticmethod
    def _query_llm_similarity(case1: TestCase, case2: TestCase) -> bool:
        """
        Sends two TestCase objects to the LLM in JSON format with a detailed prompt
        and returns a 'is_same' = true/false response.
        """
        case1_json = case1.model_dump()
        case2_json = case2.model_dump()

        prompt_text = f"""
You are given two test cases, each with a certain set of fields: 
- ScenarioID
- TestCaseID
- Title
- Description
- Objective

You will decide whether these two test cases are “contextually the same” based on the following criteria:

1. If both have the same Title (case-insensitive) OR their Titles are substantially similar in meaning,
2. AND they have either the same or very similar Description and/or Objective,
3. AND they serve essentially the same testing purpose for the same or very closely related scenarios,
4. THEN you should conclude that these two test cases are the same.

Otherwise, they are considered different.

Below are the two test cases in JSON format:

TestCase1:
{json.dumps(case1_json, indent=2, ensure_ascii=False)}

TestCase2:
{json.dumps(case2_json, indent=2, ensure_ascii=False)}

Return your response **only** in valid JSON with the following format:

{{
  "is_same": <true or false>
}}

Where:
- is_same = true if the test cases meet the criteria above
- is_same = false otherwise

Important:
- Do not provide any additional text outside the JSON object.
- Do not explain your reasoning, only provide the final JSON response.
"""

        # Messages to be sent to the chat
        messages = [
            {
                "role": "user",
                "content": prompt_text.strip()
            }
        ]

        response = chat(
            messages=messages,
            model='llama3.2',
            format={
                "type": "object",
                "properties": {
                    "is_same": {"type": "boolean"}
                },
                "required": ["is_same"]
            },
        )

        # Retrieve and parse the response as JSON
        content = response.get('message', {}).get('content', '').strip()
        try:
            parsed_content = json.loads(content)
            return parsed_content.get("is_same", False)
        except json.JSONDecodeError:
            raise ValueError(f"LLM response is not valid JSON: {content}")


# Streamlit UI
def main():
    st.set_page_config(page_title="Smart Test Case Selector", layout="wide")

    st.title("Smart Test Case Selector")
    st.markdown("""
    This application removes duplicate or similar test cases using an intelligent comparison approach.
    Upload your JSON data, view the unique test cases, and download the results.
    """)

    # File upload
    uploaded_file = st.file_uploader("Upload JSON File", type=["json"], help="Upload a JSON file containing your test cases.")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            if not isinstance(data, list):
                raise ValueError("Uploaded JSON must be a list of test cases.")

            valid_data = []
            for item in data:
                if isinstance(item, dict):
                    try:
                        valid_data.append(TestCase(**item))
                    except Exception as e:
                        st.warning(f"Skipping invalid test case: {item}. Error: {e}")
                else:
                    st.warning(f"Skipping non-dict item: {item}")

            if not valid_data:
                raise ValueError("No valid test cases found in the uploaded file.")

            test_cases = TestCaseList(test_cases=valid_data)

            with st.expander("Uploaded Test Cases", expanded=False):
                st.json(data)

            # Smart selection
            if st.button("Run Smart Selection"):
                unique_test_cases = test_cases.smart_select()

                # Display unique test cases
                st.success("Unique test cases identified successfully!")
                with st.expander("Unique Test Cases", expanded=False):
                    st.json([case.model_dump() for case in unique_test_cases.test_cases])

                # Display similar test cases
                if unique_test_cases.duplicates:
                    st.warning("Similar test cases were found!")
                    with st.expander("Similar Test Cases", expanded=False):
                        st.json(unique_test_cases.duplicates)

                # Display comparison logs
                st.info('All comparison logs are here!', icon="ℹ️")
                with st.expander("Comparison Logs", expanded=False):
                    st.json(unique_test_cases.comparison_logs)

                # Download results
                results = {
                    "unique_test_cases": [case.model_dump() for case in unique_test_cases.test_cases],
                    "similar_test_cases": unique_test_cases.duplicates,
                    "comparison_logs": unique_test_cases.comparison_logs
                }


                st.download_button(
                    label="Download Results",
                    data=json.dumps(results, indent=2),
                    file_name="smart_selection_results.json",
                    mime="application/json"
                )

        except Exception as e:
            st.error(f"Error processing file: {e}")

    else:
        st.info("Please upload a JSON file to proceed.")

if __name__ == "__main__":
    main()
