""" This script makes smart selections of test cases by eliminating similar/duplicate test cases using the LLM. """

from pydantic import BaseModel
from typing import List, Optional
from ollama import chat
import json
from datetime import datetime
import uuid

# TestCase model
class TestCase(BaseModel):
    """ Pydantic model for a test case with the following fields. """
    ScenarioID: str
    TestCaseID: str
    Title: str
    Description: Optional[str] = None
    Objective: Optional[str] = None

# TestCaseList model
class TestCaseList(BaseModel):
    """ Pydantic model for a list of test cases with a method to make smart selections. """
    test_cases: List[TestCase]
    comparison_logs: List[dict] = []  # List to store comparison results

    def smart_select(self):
        """
        Removes test cases from the list that are identified as similar/the same by the LLM.
        Returns a new list consisting of unique test cases.
        """
        unique_cases = []
        step = 1  # Counter to track comparison steps

        for case in self.test_cases:
            is_duplicate = False
            for unique_case in unique_cases:
                comparison_result = self._query_llm_similarity(case, unique_case)

                # Add the comparison result to the comparison_logs list
                self.comparison_logs.append({
                    "Step": step,
                    "ProcessName": str(uuid.uuid4()),
                    "Timestamp": datetime.now().isoformat(),
                    "Case1": case.model_dump(),
                    "Case2": unique_case.model_dump(),
                    "is_same": comparison_result,
                })
                step += 1

                # If the LLM determines the cases are "the same," skip adding this case and exit the loop
                if comparison_result:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_cases.append(case)

        return TestCaseList(test_cases=unique_cases, comparison_logs=self.comparison_logs)

    @staticmethod
    def _query_llm_similarity(case1: TestCase, case2: TestCase) -> bool:
        """
        Sends two TestCase objects to the LLM in JSON format with a detailed prompt
        and returns a 'is_same' = true/false response.
        """
        case1_json = case1.model_dump()
        case2_json = case2.model_dump()

        # Enhanced prompt
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
            model='llama3.2',  # Example model name; replace with your own model if applicable
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


if __name__ == "__main__":
    # JSON Data (some fields may be missing)
    json_data = [
        {
            "ScenarioID": "Scenario_1",
            "TestCaseID": "TestCase_1",
            "Title": "Verify Login Functionality",
            "Description": "Test the login functionality to ensure users can log in with valid credentials "
                           "and receive appropriate error messages for invalid inputs.",
            "Objective": "Validate user authentication mechanism."
        },
        {
            "ScenarioID": "Scenario_1",
            "TestCaseID": "TestCase_2",
            "Title": "Check User Login",
            "Description": "Ensure that users can log in using valid credentials "
                           "and receive proper feedback when entering incorrect credentials.",
            "Objective": "Validate login and session management."
        },
        {
            "ScenarioID": "Scenario_2",
            "TestCaseID": "TestCase_3",
            "Title": "Verify Password Reset",
            "Description": "Ensure the password reset functionality sends an email to the user when they "
                           "provide a registered email address.",
        },
        {
            "ScenarioID": "Scenario_3",
            "TestCaseID": "TestCase_4",
            "Title": "Verify Profile Update",
            "Objective": "Test user profile management."
        },
        {
            "ScenarioID": "Scenario_4",
            "TestCaseID": "TestCase_5",
            "Title": "Verify Login Functionality",
        }
    ]

    # Convert data to TestCase objects using Pydantic
    test_cases = TestCaseList(test_cases=[TestCase(**item) for item in json_data])

    # Eliminate similar/duplicate test cases and retain only unique ones
    unique_test_cases = test_cases.smart_select()

    # Print to the console
    print("Unique Test Cases:")
    for test_case in unique_test_cases.test_cases:
        print(test_case.model_dump_json(indent=2))

    # Save results to a JSON file
    results = {
        "unique_test_cases": [test_case.model_dump() for test_case in unique_test_cases.test_cases],
        "comparison_logs": unique_test_cases.comparison_logs
    }

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nComparison Logs saved to 'results.json'")
