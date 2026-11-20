
import re
import string
import streamlit as st

import json
import csv
import io
import hashlib

from document_loader import extract_text
from text_chunker import split_text
from scope_agent import extract_scope
from risk_agent import detect_risks
from action_item_agent import identify_blockers_and_actions
from documentation_agent import generate_documentation
from health_scoring import calculate_health_score



from conversational_agent import (
    build_knowledge_base,
    ask_project_question,
    generate_project_answer
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="AI Project Intelligence & Risk Advisor",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = None

if "processed_files_hash" not in st.session_state:
    st.session_state.processed_files_hash = None


# --------------------------------------------------
# APPLICATION TITLE
# --------------------------------------------------

st.title("AI Project Intelligence & Risk Advisor")

st.write(
    "Upload project documents to generate one consolidated "
    "analysis report across all uploaded files."
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def records_to_csv(records):

    if not records:
        return ""

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=records[0].keys()
    )

    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()


def normalize_text(value):

    text = str(value).lower().strip()

    text = re.sub(r"^\s*[-*•\d.)]+\s*", "", text)

    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )

    text = " ".join(text.split())

    return text


def deduplicate_documents(documents):

    seen_lines = set()
    cleaned_documents = []
    duplicate_count = 0

    for filename, content in documents:

        unique_lines = []

        for line in content.splitlines():

            original_line = line.strip()

            if not original_line:
                continue

            normalized_line = normalize_text(original_line)

            if not normalized_line:
                continue

            if normalized_line in seen_lines:

                duplicate_count += 1
                continue

            seen_lines.add(normalized_line)
            unique_lines.append(original_line)

        if unique_lines:

            cleaned_documents.append(
                "\n".join(unique_lines)
            )

    cleaned_text = "\n\n".join(cleaned_documents)

    return cleaned_text, duplicate_count


def add_unique(items, item):

    if item is None:
        return

    if isinstance(item, dict):

        key = normalize_text(
            " ".join(
                f"{k}: {v}"
                for k, v in item.items()
                if v is not None
            )
        )

    else:

        key = normalize_text(item)

    if not key:
        return

    for existing in items:

        if isinstance(existing, dict):

            existing_key = normalize_text(
                " ".join(
                    f"{k}: {v}"
                    for k, v in existing.items()
                    if v is not None
                )
            )

        else:

            existing_key = normalize_text(existing)

        if existing_key == key:
            return

    items.append(item)


def to_list(result):

    if result is None:
        return []

    if isinstance(result, list):
        return result

    if isinstance(result, tuple):
        return list(result)

    if isinstance(result, dict):

        return [
            {"category": key, "details": value}
            for key, value in result.items()
            if value is not None
        ]

    if isinstance(result, str):

        return [result] if result.strip() else []

    return [str(result)]


def display_item(item):

    if isinstance(item, dict):

        for key, value in item.items():

            if value is not None:

                label = str(key).replace(
                    "_", " "
                ).title()

                st.write(f"**{label}:** {value}")

    else:

        st.write(str(item))


def extract_document_content(uploaded_file):

    filename = uploaded_file.name
    file_bytes = uploaded_file.getvalue()

    try:

        text = extract_text(
            filename,
            file_bytes
        )

        if isinstance(text, str) and text.strip():
            return text.strip()

        return ""

    except Exception as error:

        st.warning(
            f"Text extraction failed for {filename}: {error}"
        )

        return ""


def get_uploaded_files_hash(files):

    file_hash = hashlib.sha256()

    for uploaded_file in files:

        file_hash.update(
            uploaded_file.name.encode("utf-8")
        )

        file_hash.update(
            uploaded_file.getvalue()
        )

    return file_hash.hexdigest()


# --------------------------------------------------
# DOCUMENT UPLOAD
# --------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True,
)


if not uploaded_files:

    st.session_state.knowledge_base = None
    st.session_state.processed_files_hash = None

    st.info(
        "Upload one or more project documents to begin."
    )

    st.stop()


st.write(f"**Files uploaded:** {len(uploaded_files)}")

for uploaded_file in uploaded_files:

    st.write(f"📄 {uploaded_file.name}")


# Check whether the uploaded documents have changed.

current_files_hash = get_uploaded_files_hash(
    uploaded_files
)

if (
    st.session_state.processed_files_hash is not None
    and st.session_state.processed_files_hash != current_files_hash
):

    st.session_state.knowledge_base = None
    st.session_state.processed_files_hash = None


# --------------------------------------------------
# GENERATE CONSOLIDATED REPORT
# --------------------------------------------------

if st.button(
    "Generate Consolidated Report",
    type="primary"
):

    all_documents = []
    successful_files = []

    # --------------------------------------------------
    # STEP 1: DOCUMENT EXTRACTION
    # --------------------------------------------------

    st.header("1. Document Extraction")

    with st.spinner("Extracting uploaded documents..."):

        for uploaded_file in uploaded_files:

            document_text = extract_document_content(
                uploaded_file
            )

            if document_text:

                all_documents.append(
                    (uploaded_file.name, document_text)
                )

                successful_files.append(
                    uploaded_file.name
                )

    if not all_documents:

        st.session_state.knowledge_base = None
        st.session_state.processed_files_hash = None

        st.error(
            "No readable text could be extracted "
            "from the uploaded documents."
        )

        st.stop()

    st.success(
        f"Successfully extracted {len(successful_files)} "
        f"out of {len(uploaded_files)} documents."
    )

    # --------------------------------------------------
    # STEP 2: REMOVE DUPLICATE CONTENT
    # --------------------------------------------------

    st.header("2. Duplicate Content Removal")

    original_text = "\n\n".join(
        content for _, content in all_documents
    )

    cleaned_text, duplicate_count = deduplicate_documents(
        all_documents
    )

    st.write(
        f"**Original text length:** "
        f"{len(original_text):,} characters"
    )

    st.write(
        f"**Cleaned text length:** "
        f"{len(cleaned_text):,} characters"
    )

    st.write(
        f"**Repeated lines removed:** {duplicate_count}"
    )

    if duplicate_count > 0:

        st.success(
            "Repeated content was removed while "
            "preserving unique lines."
        )

    else:

        st.info(
            "No exact repeated lines were detected."
        )

    # --------------------------------------------------
    # STEP 3: TEXT CHUNKING
    # --------------------------------------------------

    st.header("3. Document Processing")

    try:

        chunks = split_text(
            cleaned_text,
            chunk_size=500,
            overlap=50,
        )

        if chunks is None:
            chunks = []

        st.write(
            f"**Chunks generated:** {len(chunks)}"
        )

        with st.expander("View generated text chunks"):

            for index, chunk in enumerate(
                chunks,
                start=1
            ):

                chunk_text = (
                    chunk
                    if isinstance(chunk, str)
                    else str(chunk)
                )

                st.markdown(
                    f"**Chunk {index}**"
                )

                st.code(
                    chunk_text,
                    language=None
                )

                st.caption(
                    f"Characters: {len(chunk_text)}"
                )

    except Exception as error:

        st.error(
            f"Text chunking failed: {error}"
        )

        chunks = []

    # --------------------------------------------------
    # BUILD KNOWLEDGE BASE
    # --------------------------------------------------

    if chunks:

        try:

            with st.spinner(
                "Building conversational knowledge base..."
            ):

                knowledge_base = build_knowledge_base(
                    chunks
                )

                st.session_state.knowledge_base = knowledge_base
                st.session_state.processed_files_hash = current_files_hash

            st.success(
                "Conversational knowledge base created successfully."
            )

        except Exception as error:

            st.session_state.knowledge_base = None
            st.session_state.processed_files_hash = None

            st.error(
                f"Knowledge base creation failed: {error}"
            )

    else:

        st.session_state.knowledge_base = None
        st.session_state.processed_files_hash = None

        st.warning(
            "No chunks are available to build the knowledge base."
        )

    # --------------------------------------------------
    # CONSOLIDATED ANALYSIS
    # --------------------------------------------------

    st.divider()

    st.header("4. Consolidated Analysis Report")

    scope_results = {}
    unique_risks = []
    blockers = []
    action_items = []

    # --------------------------------------------------
    # STEP 4: SCOPE ANALYSIS
    # --------------------------------------------------

    st.subheader("1. Scope and Deliverables")

    try:

        scope_results = extract_scope(cleaned_text)

        if isinstance(scope_results, dict):

            for category, details in scope_results.items():

                st.markdown(
                    f"**{str(category).replace('_', ' ').title()}**"
                )

                if isinstance(details, (list, tuple)):

                    if details:

                        for detail in details:
                            st.write(f"- {detail}")

                    else:

                        st.write(
                            "No matching information found."
                        )

                elif details:

                    st.write(details)

                else:

                    st.write(
                        "No matching information found."
                    )

        elif scope_results:

            for item in to_list(scope_results):
                display_item(item)

        else:

            st.info(
                "No scope information was detected."
            )

    except Exception as error:

        st.error(
            f"Scope analysis failed: {error}"
        )

    # --------------------------------------------------
    # STEP 5: RISK DETECTION
    # --------------------------------------------------

    st.subheader("2. Risk Detection")

    try:

        raw_risks = detect_risks(cleaned_text)

        for risk in to_list(raw_risks):
            add_unique(unique_risks, risk)

        if unique_risks:

            st.write(
                f"**Unique risks detected: "
                f"{len(unique_risks)}**"
            )

            for index, risk in enumerate(
                unique_risks,
                start=1
            ):

                with st.container(border=True):

                    st.markdown(
                        f"**Risk {index}**"
                    )

                    display_item(risk)

        else:

            st.info(
                "No risks were detected."
            )

    except Exception as error:

        st.error(
            f"Risk detection failed: {error}"
        )

    # --------------------------------------------------
    # STEP 6: BLOCKERS AND ACTION ITEMS
    # --------------------------------------------------

    st.subheader("3. Blockers and Action Items")

    try:

        action_results = identify_blockers_and_actions(
            cleaned_text
        )

        blockers = []
        action_items = []

        if isinstance(action_results, dict):

            raw_blockers = action_results.get(
                "blockers",
                action_results.get(
                    "identified_blockers",
                    []
                ),
            )

            raw_actions = action_results.get(
                "action_items",
                action_results.get(
                    "actions",
                    action_results.get(
                        "identified_actions",
                        []
                    ),
                ),
            )

            for item in to_list(raw_blockers):
                add_unique(blockers, item)

            for item in to_list(raw_actions):
                add_unique(action_items, item)

        elif (
            isinstance(action_results, tuple)
            and len(action_results) == 2
        ):

            for item in to_list(action_results[0]):
                add_unique(blockers, item)

            for item in to_list(action_results[1]):
                add_unique(action_items, item)

        elif action_results:

            for item in to_list(action_results):
                add_unique(action_items, item)

        # DISPLAY BLOCKERS

        st.markdown("**Identified Blockers**")

        if blockers:

            for index, blocker in enumerate(
                blockers,
                start=1
            ):

                st.markdown(
                    f"**Blocker {index}**"
                )

                display_item(blocker)

        else:

            st.info(
                "No blockers were detected."
            )

        # DISPLAY ACTION ITEMS

        st.markdown("**Action Items**")

        if action_items:

            for index, action in enumerate(
                action_items,
                start=1
            ):

                st.markdown(
                    f"**Action {index}**"
                )

                display_item(action)

        else:

            st.info(
                "No action items were detected."
            )

    except Exception as error:

        st.error(
            f"Blocker and action item analysis failed: {error}"
        )

    # --------------------------------------------------
    # STEP 7: DOCUMENTATION GENERATION
    # --------------------------------------------------

    st.divider()

    st.header("5. Documentation Generation")

    try:

        documentation = generate_documentation(
            scope_results,
            unique_risks,
            action_items
        )

        if not isinstance(documentation, dict):
            documentation = {}

        user_stories = documentation.get(
            "user_stories", []
        ) or []

        risk_register = documentation.get(
            "risk_register", []
        ) or []

        action_report = documentation.get(
            "action_item_report", []
        ) or []

        # USER STORIES

        st.subheader("1. Generated User Stories")

        if user_stories:

            st.dataframe(
                user_stories,
                width="stretch",
                hide_index=True
            )

            st.download_button(
                label="Download User Stories (CSV)",
                data=records_to_csv(user_stories),
                file_name="user_stories.csv",
                mime="text/csv"
            )

        else:

            st.warning(
                "No user stories could be generated."
            )

        # RISK REGISTER

        st.subheader("2. Generated Risk Register")

        if risk_register:

            st.dataframe(
                risk_register,
                width="stretch",
                hide_index=True
            )

            st.download_button(
                label="Download Risk Register (CSV)",
                data=records_to_csv(risk_register),
                file_name="risk_register.csv",
                mime="text/csv"
            )

        else:

            st.warning(
                "No risk register entries were generated."
            )

        # ACTION ITEM REPORT

        st.subheader("3. Generated Action Item Report")

        if action_report:

            st.dataframe(
                action_report,
                width="stretch",
                hide_index=True
            )

            st.download_button(
                label="Download Action Item Report (CSV)",
                data=records_to_csv(action_report),
                file_name="action_item_report.csv",
                mime="text/csv"
            )

        else:

            st.warning(
                "No action item report entries were generated."
            )

        # COMPLETE DOCUMENTATION DOWNLOAD

        st.subheader("Download Complete Documentation")

        documentation_json = json.dumps(
            documentation,
            indent=4,
            ensure_ascii=False
        )

        st.download_button(
            label="Download All Documentation (JSON)",
            data=documentation_json,
            file_name="project_documentation.json",
            mime="application/json",
            type="primary"
        )

        if user_stories or risk_register or action_report:

            st.success(
                "Documentation generation completed."
            )

        else:

            st.error(
                "Documentation generation returned empty results."
            )

    except Exception as error:

        st.error(
            f"Documentation generation failed: {error}"
        )

    # --------------------------------------------------
    # STEP 8: PROJECT HEALTH SCORING
    # --------------------------------------------------

    st.divider()

    st.header("6. Project Health Score")

    try:

        health = calculate_health_score(
            scope_results,
            unique_risks,
            blockers
        )

        overall_score = health["overall_score"]

        st.subheader("Overall Project Health")

        st.metric(
            label="Project Health Score",
            value=f"{overall_score}/100",
            delta=health["health_status"]
        )

        st.progress(
            max(0, min(100, overall_score)) / 100
        )

        st.subheader("Health Score Breakdown")

        health_breakdown = [
            {
                "Dimension": "Scope Clarity",
                "Score": health["scope_score"],
                "Maximum Score": health["scope_max"]
            },
            {
                "Dimension": "Timeline Health",
                "Score": health["timeline_score"],
                "Maximum Score": health["timeline_max"]
            },
            {
                "Dimension": "Blocker Status",
                "Score": health["blocker_score"],
                "Maximum Score": health["blocker_max"]
            }
        ]

        st.dataframe(
            health_breakdown,
            width="stretch",
            hide_index=True
        )

        st.subheader("Detected Project Concerns")

        st.write(
            f"Schedule risks detected: "
            f"{health['schedule_risks']}"
        )

        st.write(
            f"Blockers detected: "
            f"{health['blocker_count']}"
        )

        if health["milestone_conflict"]:

            st.warning(
                "Conflicting testing milestones detected. "
                "The documents mention different testing weeks."
            )

        if health["health_status"] == "Healthy":

            st.success(
                "The project is currently healthy."
            )

        elif health["health_status"] == "Moderate":

            st.warning(
                "The project needs attention."
            )

        else:

            st.error(
                "The project is at risk."
            )

    except Exception as error:

        st.error(
            f"Health scoring failed: {error}"
        )

    # --------------------------------------------------
    # STEP 9: PROCESSING SUMMARY
    # --------------------------------------------------

    st.divider()

    st.subheader("7. Processing Summary")

    st.write(
        f"- Files uploaded: {len(uploaded_files)}"
    )

    st.write(
        f"- Files successfully extracted: "
        f"{len(successful_files)}"
    )

    st.write(
        f"- Repeated lines removed: {duplicate_count}"
    )

    st.write(
        f"- Cleaned text length: "
        f"{len(cleaned_text):,} characters"
    )

    st.write(
        f"- Text chunks generated: {len(chunks)}"
    )

    st.write(
        f"- Unique risks detected: {len(unique_risks)}"
    )

    st.write(
        f"- Blockers detected: {len(blockers)}"
    )

    st.write(
        f"- Action items detected: {len(action_items)}"
    )

    with st.expander("View successfully processed files"):

        for filename in successful_files:
            st.write(f"- {filename}")

    with st.expander("View cleaned consolidated text"):

        st.text(cleaned_text)



# --------------------------------------------------
# STEP 10: CONVERSATIONAL PROJECT INTELLIGENCE ASSISTANT
# --------------------------------------------------

st.divider()

st.header("8. Conversational Project Intelligence Assistant")

st.write(
    "Ask questions about your uploaded project documents. "
    "The assistant retrieves relevant information from the documents."
)

if st.session_state.knowledge_base:

    with st.form(key="project_question_form"):

        question = st.text_input(
            "Enter your project-related question:",
            placeholder="Example: Why is testing delayed?",
            key="project_question_input"
        )

        submit_question = st.form_submit_button(
            "Ask Question"
        )

    if submit_question:

        if not question.strip():

            st.warning("Please enter a question.")

        else:

            try:

                with st.spinner("Searching project documents..."):

                    results = ask_project_question(
                        question,
                        st.session_state.knowledge_base,
                        top_k=3
                    )
                    answer_data = generate_project_answer(
                        question,
                        results
                    )

                st.subheader("Generated Answer")

                st.write(answer_data["answer"])

                st.markdown("### Key Findings")

                for finding in answer_data["key_findings"]:
                    st.markdown(f"- {finding}")

                if answer_data["suggested_actions"]:

                    st.markdown("### Related Action Items")

                    for action in answer_data["suggested_actions"]:
                        st.markdown(f"- {action}")

                if results:

                    st.subheader("Retrieved Information")

                    for number, result in enumerate(results, start=1):

                        st.markdown(
                            f"**Relevant Excerpt {number}**"
                        )

                        st.write(result["chunk"])

                        st.caption(
                            f"Similarity score: {result['score']:.3f}"
                        )

                else:

                    st.warning(
                        "No relevant information was found."
                    )

            except Exception as error:

                st.error(
                    f"Unable to answer the question: {error}"
                )

else:

    st.info(
        "Upload and process project documents to use the assistant."
    )
