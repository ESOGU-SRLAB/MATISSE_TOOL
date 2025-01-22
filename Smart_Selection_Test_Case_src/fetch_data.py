import streamlit as st
from pymongo import MongoClient
import os

# MongoDB bağlantısı
MONGO_URI = os.getenv("MONGO_URI")  # Ortam değişkeninden URI al
client = MongoClient(MONGO_URI)
db = client["modular_test_scenario_gen"]
collection = db["sessions"]

def fetch_valid_combinations():
    """
    MongoDB'den benzersiz (process_title, selected_category, selected_test_type) kombinasyonlarını getirir.
    None değerlerini filtreler.
    """
    data = collection.find(
        {}, 
        {"process_title": 1, "selected_category": 1, "selected_test_type": 1}
    )
    combinations = [
        {
            "process_title": entry.get("process_title"),
            "selected_category": entry.get("selected_category"),
            "selected_test_type": entry.get("selected_test_type")
        }
        for entry in data
        if entry.get("process_title") and entry.get("selected_category") and entry.get("selected_test_type")
    ]
    return combinations

def fetch_details_by_combination(process_title, selected_category, selected_test_type):
    """
    Seçilen (process_title, selected_category, selected_test_type) kombinasyonuna göre detayları getirir.
    """
    data = collection.find_one(
        {
            "process_title": process_title,
            "selected_category": selected_category,
            "selected_test_type": selected_test_type
        },
        {
            "process_title": 1,
            "selected_category": 1,
            "selected_test_type": 1,
            "model_output.TestCases": 1
        }
    )
    return data

# Streamlit UI
st.title("Filtered Process Titles, Categories, and Types Viewer")

# Session state kontrolü
if "selected_test_cases" not in st.session_state:
    st.session_state.selected_test_cases = {}

# Veritabanındaki geçerli kombinasyonları getir
combinations = fetch_valid_combinations()

if combinations:
    # Selectbox için mevcut kombinasyonları hazırla
    options = [
        f"{entry['process_title']} - {entry['selected_test_type']} - {entry['selected_category']}"
        for entry in combinations
    ]
    # Varsayılan seçenek eklenir
    options.insert(0, "Select a Process Title - Test Type - Category")

    selected_option = st.selectbox("Select a Process Title - Test Type - Category:", options)

    # Eğer varsayılan seçenek seçilmişse hiçbir işlem yapılmaz
    if selected_option != "Select a Process Title - Test Type - Category":
        # Seçilen kombinasyonun detaylarını getirme
        selected_index = options.index(selected_option) - 1  # Varsayılanı hesaba kat
        selected_entry = combinations[selected_index]

        process_title = selected_entry["process_title"]
        selected_category = selected_entry["selected_category"]
        selected_test_type = selected_entry["selected_test_type"]

        # Detayları getir ve göster
        details = fetch_details_by_combination(process_title, selected_category, selected_test_type)

        if details:
            st.subheader(f"Details for: {details['process_title']}")
            st.write(f"- **Selected Category**: {details['selected_category']}")
            st.write(f"- **Selected Test Type**: {details['selected_test_type']}")

            # TestCases bilgilerini göster
            test_cases = details.get("model_output", {}).get("TestCases", [])
            if test_cases:
                st.write("### Test Cases")
                for case_group in test_cases:
                    scenario_id = case_group.get("scenario_id", "Unknown Scenario")
                    st.write(f"#### Scenario: {scenario_id}")

                    testcases = case_group.get("test_case", {}).get("TestCases", [])
                    if testcases:
                        for idx, case in enumerate(testcases):
                            case_id = case.get("TestCaseID", f"Unknown_ID_{idx}")
                            title = case.get("Title", "No Title")
                            description = case.get("Description", "No Description")
                            objective = case.get("Objective", "No Objective")
                            category = case.get("Category", "No Category")
                            comments = case.get("Comments", "No Comments")

                            # Benzersiz anahtar
                            unique_key = f"{scenario_id}_{case_id}"

                            # Seçim durumunu session_state'e yaz
                            if unique_key not in st.session_state.selected_test_cases:
                                st.session_state.selected_test_cases[unique_key] = False

                            # Checkbox oluştur ve durumunu koru
                            selected = st.checkbox(
                                f"{case_id}: {title}",
                                key=unique_key,
                                value=st.session_state.selected_test_cases[unique_key]
                            )

                            st.session_state.selected_test_cases[unique_key] = selected

                            # Test case detaylarını yazdır
                            st.write(f"- **Description**: {description}")
                            st.write(f"- **Objective**: {objective}")
                            st.write(f"- **Category**: {category}")
                            st.write(f"- **Comments**: {comments}")
                            st.write("---")
                    else:
                        st.write("No Test Cases Found for this Scenario.")
            else:
                st.write("No Test Cases Found.")
        else:
            st.write("No details found for the selected combination.")

    # Seçilenleri gösterme butonu
    if st.button("Show Selected Test Cases"):
        st.write("### Selected Test Cases")
        for key, selected in st.session_state.selected_test_cases.items():
            if selected:
                st.write(f"- {key}")
else:
    st.write("No valid combinations found in the database.")
