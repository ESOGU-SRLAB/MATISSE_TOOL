import json

def extract_and_save_json(input_str, filename):
    stack = []
    json_start = -1
    for i, char in enumerate(input_str):
        if char == '{':
            if not stack:
                json_start = i
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    json_end = i + 1
                    try:
                        json_obj = json.loads(input_str[json_start:json_end])
                        with open(filename, 'w') as json_file:
                            json.dump(json_obj, json_file, indent=2)
                        return f"Extracted JSON saved to {filename}"
                    except json.JSONDecodeError:
                        continue
    return "No valid JSON found in the input."
