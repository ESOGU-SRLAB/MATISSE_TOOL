## How It Works?

1. **Initially**, we have a pile of test cases (with information like titles, descriptions, etc.).

2. We create an **empty list called "Unique Test Case List"** (let's name it `unique_cases`).

3. **We iterate through all the test cases**. For each new test case (e.g., `NewCase`):  
   - First, we wonder, "Is there already an identical case?" Since we don't know yet, we set `is_duplicate = False`.  
   - Then, we compare `NewCase` with each **already added unique test case** (`unique_case`). Each time, we ask the LLM:  
     > "Are these two test cases the same or different?"  
   - The LLM responds with `true` (same) or `false` (different).  

4. **If the LLM says "Same!"**:  
   - We conclude, "This new case already exists, so no need to add it."  
   - We skip any further action for this case and move on to the next test case.  

5. **If the LLM always says "Different!"**, meaning the new case does not resemble any previously added case:  
   - We conclude, "This new case is truly unique!" and add it to the `unique_cases` list.  

6. **Once all test cases are processed**, we are left with a list of test cases we consider "unique."  
   - If a case is found to be similar to an already added case (marked as "Same" by the LLM), it is **not added** to the list again.  

7. **As a result**, we have a list of "unique" test cases in one place. The code also keeps a log of which test cases were compared with which, and whether the LLM marked them as "Same/Different." This allows us to look back and answer the question: "Why was this case excluded?"

---

## Summary

- We start with an input list (all test cases).  
- For each new case, we compare it with the already added "Unique List" one by one.  
- The comparison is not manual; an AI model (LLM) answers the question, "Are these two cases the same?"  
- If the LLM says "Same," the new case is not added. If the LLM says "Different," the new case is added.  
- In the end, the final list contains only those that were not excluded (i.e., those the LLM found to be "different").

```mermaid
flowchart TB
    A("Start") --> B["Load all test cases"]
    B --> C["Unique List (unique_cases) = [] (empty)"]
    C --> D["Start processing each test case"]
    D --> E["Process test case <br/> is_duplicate = False"]
    E --> F{"Is there a case<br/> already in Unique List?"}
    F -- "Yes" --> G["Ask LLM: <br/> 'Are these two test cases the same?'"]
    G --> H{"is_same = True?"}
    H -- "Yes" --> I["Marked as same → is_duplicate = True<br/> Stop comparison"]
    H -- "No" --> J["Continue comparing with <br/> another unique_case"]
    I --> K
    J --> F
    F -- "No, none <br/> or all checked" --> K["If is_duplicate = False <br/> Add to Unique List"]
    K --> L{"Are there more test cases?"}
    L -- "Yes" --> D
    L -- "No" --> M["Unique Test Case List is ready"]
    M --> N("End")
