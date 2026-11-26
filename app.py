
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
from risk_agent import detect_risks, reconcile_risks
from action_item_agent import identify_blockers_and_actions
from documentation_agent import generate_documentation
from health_scoring import calculate_health_score

from conversational_agent import (
    build_knowledge_base,
    add_chunks_to_knowledge_base,
    ask_project_question,
    generate_project_answer,
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
# SESSION STATE
# --------------------------------------------------

DEFAULT_STATE = {
    "knowledge_base": None,
    "processed_documents": {},
    "analysis_results": None,
    "last_qa": None,
}

for state_key, default_value in DEFAULT_STATE.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# --------------------------------------------------
# APPLICATION TITLE
# --------------------------------------------------

st.title("AI Project Intelligence & Risk Advisor")

st.write(
    "Upload project documents to build a persistent project knowledge base, "
    "generate consolidated analysis, and ask questions about the project."
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

    text = re.sub(
        r"^\s*[-*•\d.)]+\s*",
        "",
        text
    )

    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )

    return " ".join(text.split())


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
                label = str(key).replace("_", " ").title()
                st.write(f"**{label}:** {value}")
    else:
        st.write(str(item))


def extract_document_content(filename, file_bytes):
    try:
        text = extract_text(filename, file_bytes)

        if isinstance(text, str) and text.strip():
            return text.strip()

        return ""

    except Exception as error:
        st.warning(
            f"Text extraction failed for {filename}: {error}"
        )
        return ""


def get_file_hash(uploaded_file):
    digest = hashlib.sha256()

    digest.update(
        uploaded_file.name.encode("utf-8")
    )

    digest.update(
        uploaded_file.getvalue()
    )

    return digest.hexdigest()


def deduplicate_documents(documents):
    """Remove repeated non-empty lines across the complete document collection."""

    seen_lines = set()
    cleaned_documents = []
    duplicate_count = 0

    for _, content in documents:
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

    return (
        "\n\n".join(cleaned_documents),
        duplicate_count
    )


# --------------------------------------------------
# CONSOLIDATED PROJECT ANALYSIS
# --------------------------------------------------

def run_consolidated_analysis(cleaned_text):
    """Run all project agents and reconcile current blocker/risk status."""

    scope_results = {}
    unique_risks = []
    active_blockers = []
    resolved_blockers = []
    blocker_status = []
    action_items = []
    documentation = {}
    health = None
    errors = {}

    # 1. Scope and deliverables

    try:
        scope_results = extract_scope(cleaned_text)

    except Exception as error:
        errors["scope"] = str(error)

    # 2. Risk detection and status reconciliation

    try:
        raw_risks = detect_risks(cleaned_text)

        for risk in to_list(raw_risks):
            add_unique(unique_risks, risk)

        unique_risks = reconcile_risks(
            cleaned_text,
            unique_risks,
        )

    except Exception as error:
        errors["risks"] = str(error)

    # 3. Blocker status and action-item extraction

    try:
        action_results = identify_blockers_and_actions(
            cleaned_text
        )

        if isinstance(action_results, dict):

            raw_blockers = action_results.get(
                "blockers", []
            )

            raw_resolved = action_results.get(
                "resolved_blockers", []
            )

            raw_status = action_results.get(
                "blocker_status", []
            )

            raw_actions = action_results.get(
                "action_items",
                action_results.get(
                    "actions",
                    action_results.get(
                        "identified_actions", []
                    ),
                ),
            )

            for item in to_list(raw_blockers):
                add_unique(active_blockers, item)

            for item in to_list(raw_resolved):
                add_unique(resolved_blockers, item)

            for item in to_list(raw_status):
                add_unique(blocker_status, item)

            for item in to_list(raw_actions):
                add_unique(action_items, item)

        elif isinstance(action_results, tuple) and len(action_results) == 2:

            for item in to_list(action_results[0]):
                add_unique(active_blockers, item)

            for item in to_list(action_results[1]):
                add_unique(action_items, item)

        elif action_results:

            for item in to_list(action_results):
                add_unique(action_items, item)

    except Exception as error:
        errors["blockers_and_actions"] = str(error)

    # 4. Documentation generation

    try:
        documentation = generate_documentation(
            scope_results,
            unique_risks,
            action_items,
        )

        if not isinstance(documentation, dict):
            documentation = {}

    except Exception as error:
        errors["documentation"] = str(error)

    # 5. Health scoring uses active blockers only

    try:
        health = calculate_health_score(
            scope_results,
            unique_risks,
            active_blockers,
        )

    except Exception as error:
        errors["health"] = str(error)

    return {
        "scope_results": scope_results,
        "risks": unique_risks,
        "blockers": active_blockers,
        "resolved_blockers": resolved_blockers,
        "blocker_status": blocker_status,
        "action_items": action_items,
        "documentation": documentation,
        "health": health,
        "errors": errors,
        "cleaned_text": cleaned_text,
    }


# --------------------------------------------------
# DISPLAY FUNCTIONS
# --------------------------------------------------

def render_scope_summary(scope_results):

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
                    st.write("No matching information found.")

            elif details:
                st.write(details)

            else:
                st.write("No matching information found.")

    elif scope_results:

        for item in to_list(scope_results):
            display_item(item)

    else:
        st.info("No scope information was detected.")


def render_list_of_items(items, item_label):

    if not items:
        st.info(
            f"No {item_label.lower()} detected."
        )
        return

    for index, item in enumerate(items, start=1):

        st.markdown(
            f"**{item_label} {index}**"
        )

        display_item(item)


# --------------------------------------------------
# DOCUMENT UPLOAD
# --------------------------------------------------

uploaded_files = st.file_uploader(
    "Upload project documents",
    type=["pdf", "docx", "csv", "txt"],
    accept_multiple_files=True,
    help=(
        "You can upload additional documents later. Previously processed "
        "documents remain in this session even if they are no longer selected."
    ),
)


if uploaded_files:

    st.write(
        f"**Files selected in this upload:** {len(uploaded_files)}"
    )

    for uploaded_file in uploaded_files:
        st.write(f"📄 {uploaded_file.name}")


st.caption(
    f"Documents retained in this session: "
    f"{len(st.session_state.processed_documents)}"
)


# --------------------------------------------------
# PROCESS NEW DOCUMENTS / UPDATE KNOWLEDGE BASE
# --------------------------------------------------

if st.button(
    "Process New Documents / Update Project",
    type="primary"
):

    new_documents = []
    new_chunks = []
    extraction_failures = []
    duplicate_uploads = 0

    with st.spinner(
        "Checking and extracting newly uploaded documents..."
    ):

        for uploaded_file in uploaded_files or []:

            file_hash = get_file_hash(uploaded_file)

            if file_hash in st.session_state.processed_documents:
                duplicate_uploads += 1
                continue

            document_text = extract_document_content(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )

            if not document_text:
                extraction_failures.append(
                    uploaded_file.name
                )
                continue

            try:

                document_chunks = split_text(
                    document_text,
                    chunk_size=500,
                    overlap=50,
                )

                document_chunks = [
                    chunk.strip()
                    for chunk in (document_chunks or [])
                    if isinstance(chunk, str) and chunk.strip()
                ]

            except Exception as error:

                st.error(
                    f"Chunking failed for {uploaded_file.name}: {error}"
                )

                continue

            new_documents.append(
                {
                    "hash": file_hash,
                    "file_name": uploaded_file.name,
                    "text": document_text,
                    "chunks": document_chunks,
                }
            )

            new_chunks.extend(document_chunks)

    # Update the existing FAISS knowledge base.

    try:

        if new_chunks:

            with st.spinner(
                "Updating the project knowledge base..."
            ):

                if st.session_state.knowledge_base is None:

                    unique_initial_chunks = list(
                        dict.fromkeys(new_chunks)
                    )

                    st.session_state.knowledge_base = (
                        build_knowledge_base(
                            unique_initial_chunks
                        )
                    )

                    kb_update = {
                        "added": len(unique_initial_chunks),
                        "skipped": (
                            len(new_chunks)
                            - len(unique_initial_chunks)
                        ),
                        "total_chunks": len(
                            st.session_state.knowledge_base["chunks"]
                        ),
                    }

                else:

                    kb_update = add_chunks_to_knowledge_base(
                        st.session_state.knowledge_base,
                        new_chunks,
                    )

        else:

            kb_update = {
                "added": 0,
                "skipped": 0,
                "total_chunks": (
                    len(st.session_state.knowledge_base["chunks"])
                    if st.session_state.knowledge_base
                    else 0
                ),
            }

        # Store document metadata only after KB update succeeds.

        for document in new_documents:

            st.session_state.processed_documents[
                document["hash"]
            ] = document

    except Exception as error:

        st.error(
            f"Knowledge base update failed: {error}"
        )

        st.stop()

    if duplicate_uploads:

        st.info(
            f"{duplicate_uploads} already-processed upload(s) were skipped."
        )

    if extraction_failures:

        st.warning(
            "Could not extract readable text from: "
            + ", ".join(extraction_failures)
        )

    if new_documents:

        st.success(
            f"Successfully processed {len(new_documents)} new document(s)."
        )

    elif not st.session_state.processed_documents:

        st.warning(
            "No readable project documents have been processed yet."
        )

    else:

        st.info(
            "No new documents were found. Re-analyzing retained documents."
        )

    st.write(
        f"**New chunks added to the knowledge base:** {kb_update['added']}"
    )

    st.write(
        f"**Duplicate chunks skipped:** {kb_update['skipped']}"
    )

    st.write(
        f"**Total knowledge-base chunks:** {kb_update['total_chunks']}"
    )

    # Consolidate all retained documents.

    retained_documents = [
        (document["file_name"], document["text"])
        for document in st.session_state.processed_documents.values()
    ]

    if retained_documents:

        original_text = "\n\n".join(
            content for _, content in retained_documents
        )

        cleaned_text, duplicate_count = deduplicate_documents(
            retained_documents
        )

        with st.spinner(
            "Running consolidated project analysis..."
        ):

            analysis = run_consolidated_analysis(
                cleaned_text
            )

        analysis["metrics"] = {
            "files_processed": len(retained_documents),
            "original_text_length": len(original_text),
            "cleaned_text_length": len(cleaned_text),
            "duplicate_lines_removed": duplicate_count,
            "knowledge_base_chunks": (
                len(st.session_state.knowledge_base["chunks"])
                if st.session_state.knowledge_base
                else 0
            ),
        }

        st.session_state.analysis_results = analysis
        st.session_state.last_qa = None

        st.success(
            "Project analysis updated successfully."
        )

    else:

        st.session_state.analysis_results = None


# --------------------------------------------------
# CLEAR SESSION DATA
# --------------------------------------------------

if st.session_state.processed_documents:

    if st.button("Clear All Processed Project Data"):

        st.session_state.knowledge_base = None
        st.session_state.processed_documents = {}
        st.session_state.analysis_results = None
        st.session_state.last_qa = None

        st.rerun()


# --------------------------------------------------
# PROJECT INSIGHTS AND RISK SUMMARY DASHBOARD
# --------------------------------------------------

analysis = st.session_state.analysis_results


if analysis:

    st.divider()

    st.header(
        "9. Project Insights and Risk Summary Dashboard"
    )

    health = analysis.get("health")
    risks = analysis.get("risks", [])
    actions = analysis.get("action_items", [])
    active_blockers = analysis.get("blockers", [])
    resolved_blockers = analysis.get("resolved_blockers", [])
    scope_results = analysis.get("scope_results", {})

    if health:

        metric_columns = st.columns(4)

        metric_columns[0].metric(
            "Project Health",
            f"{health.get('overall_score', 'N/A')}/100",
            health.get("health_status", ""),
        )

        metric_columns[1].metric(
            "Risks",
            len(risks)
        )

        metric_columns[2].metric(
            "Action Items",
            len(actions)
        )

        metric_columns[3].metric(
            "Documents",
            analysis.get("metrics", {}).get(
                "files_processed", 0
            ),
        )

        score = health.get("overall_score", 0)

        st.progress(
            max(0, min(100, score)) / 100
        )

    else:

        st.warning(
            "The project health score is not available."
        )

    with st.expander(
        "Scope Summary",
        expanded=True
    ):

        render_scope_summary(scope_results)

    dashboard_columns = st.columns(2)

    with dashboard_columns[0]:

        st.subheader("Extracted Risks")

        render_list_of_items(
            risks,
            "Risk"
        )

    with dashboard_columns[1]:

        st.subheader("Action Items")

        render_list_of_items(
            actions,
            "Action"
        )

    st.subheader("Blocker Status")

    blocker_columns = st.columns(2)

    with blocker_columns[0]:

        st.markdown("**Active Blockers**")

        render_list_of_items(
            active_blockers,
            "Active Blocker"
        )

    with blocker_columns[1]:

        st.markdown("**Resolved Blockers**")

        render_list_of_items(
            resolved_blockers,
            "Resolved Blocker"
        )

    if analysis.get("errors"):

        with st.expander("Analysis warnings"):

            for section, message in analysis["errors"].items():

                st.warning(
                    f"{section.replace('_', ' ').title()}: {message}"
                )


# --------------------------------------------------
# CONSOLIDATED ANALYSIS REPORT
# --------------------------------------------------

if analysis:

    st.divider()

    st.header("Consolidated Analysis Report")

    st.subheader("1. Scope and Deliverables")

    render_scope_summary(
        analysis.get("scope_results", {})
    )

    st.subheader("2. Risk Detection")

    risks = analysis.get("risks", [])

    st.write(
        f"**Unique risks detected: {len(risks)}**"
    )

    render_list_of_items(
        risks,
        "Risk"
    )

    st.subheader("3. Blockers and Action Items")

    st.markdown("**Active Blockers**")

    render_list_of_items(
        analysis.get("blockers", []),
        "Active Blocker"
    )

    st.markdown("**Resolved Blockers**")

    render_list_of_items(
        analysis.get("resolved_blockers", []),
        "Resolved Blocker"
    )

    st.markdown("**Action Items**")

    render_list_of_items(
        analysis.get("action_items", []),
        "Action"
    )

    # --------------------------------------------------
    # DOCUMENTATION GENERATION
    # --------------------------------------------------

    st.divider()

    st.header("Documentation Generation")

    documentation = analysis.get(
        "documentation", {}
    )

    user_stories = documentation.get(
        "user_stories", []
    ) or []

    risk_register = documentation.get(
        "risk_register", []
    ) or []

    action_report = documentation.get(
        "action_item_report", []
    ) or []

    st.subheader("1. Generated User Stories")

    if user_stories:

        st.dataframe(
            user_stories,
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download User Stories (CSV)",
            data=records_to_csv(user_stories),
            file_name="user_stories.csv",
            mime="text/csv",
        )

    else:

        st.warning(
            "No user stories could be generated."
        )

    st.subheader("2. Generated Risk Register")

    if risk_register:

        st.dataframe(
            risk_register,
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download Risk Register (CSV)",
            data=records_to_csv(risk_register),
            file_name="risk_register.csv",
            mime="text/csv",
        )

    else:

        st.warning(
            "No risk register entries were generated."
        )

    st.subheader("3. Generated Action Item Report")

    if action_report:

        st.dataframe(
            action_report,
            width="stretch",
            hide_index=True
        )

        st.download_button(
            "Download Action Item Report (CSV)",
            data=records_to_csv(action_report),
            file_name="action_item_report.csv",
            mime="text/csv",
        )

    else:

        st.warning(
            "No action item report entries were generated."
        )

    if documentation:

        st.subheader(
            "Download Complete Documentation"
        )

        st.download_button(
            "Download All Documentation (JSON)",
            data=json.dumps(
                documentation,
                indent=4,
                ensure_ascii=False,
            ),
            file_name="project_documentation.json",
            mime="application/json",
            type="primary",
        )

    # --------------------------------------------------
    # PROJECT HEALTH SCORING
    # --------------------------------------------------

    health = analysis.get("health")

    if health:

        st.divider()

        st.header("Project Health Score")

        st.metric(
            "Project Health Score",
            f"{health['overall_score']}/100",
            health["health_status"],
        )

        st.progress(
            max(0, min(100, health["overall_score"])) / 100
        )

        health_breakdown = [
            {
                "Dimension": "Scope Clarity",
                "Score": health["scope_score"],
                "Maximum Score": health["scope_max"],
            },
            {
                "Dimension": "Timeline Health",
                "Score": health["timeline_score"],
                "Maximum Score": health["timeline_max"],
            },
            {
                "Dimension": "Blocker Status",
                "Score": health["blocker_score"],
                "Maximum Score": health["blocker_max"],
            },
        ]

        st.dataframe(
            health_breakdown,
            width="stretch",
            hide_index=True,
        )

        st.subheader("Detected Project Concerns")

        st.write(
            f"Schedule risks detected: {health['schedule_risks']}"
        )

        st.write(
            f"Blockers detected: {health['blocker_count']}"
        )

        if health.get("milestone_conflict"):

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

    # --------------------------------------------------
    # PROCESSING SUMMARY
    # --------------------------------------------------

    metrics = analysis.get("metrics", {})

    st.divider()

    st.subheader("Processing Summary")

    st.write(
        f"- Files processed: {metrics.get('files_processed', 0)}"
    )

    st.write(
        f"- Repeated lines removed: "
        f"{metrics.get('duplicate_lines_removed', 0)}"
    )

    st.write(
        f"- Original text length: "
        f"{metrics.get('original_text_length', 0):,} characters"
    )

    st.write(
        f"- Cleaned text length: "
        f"{metrics.get('cleaned_text_length', 0):,} characters"
    )

    st.write(
        f"- Knowledge-base chunks: "
        f"{metrics.get('knowledge_base_chunks', 0)}"
    )

    with st.expander("View processed files"):

        for document in st.session_state.processed_documents.values():

            st.write(
                f"- {document['file_name']}"
            )

    with st.expander("View cleaned consolidated text"):

        st.text(
            analysis.get("cleaned_text", "")
        )


# --------------------------------------------------
# CONVERSATIONAL PROJECT INTELLIGENCE ASSISTANT
# --------------------------------------------------

st.divider()

st.header(
    "Conversational Project Intelligence Assistant"
)

st.write(
    "Ask questions about your uploaded project documents. "
    "The assistant retrieves relevant information from the retained knowledge base."
)


if st.session_state.knowledge_base:

    with st.form(key="project_question_form"):

        question = st.text_input(
            "Enter your project-related question:",
            placeholder="Example: Why is testing delayed?",
        )

        submit_question = st.form_submit_button(
            "Ask Question"
        )

    if submit_question:

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            try:

                with st.spinner(
                    "Searching project documents..."
                ):

                    results = ask_project_question(
                        question,
                        st.session_state.knowledge_base,
                        top_k=3,
                    )

                    answer_data = generate_project_answer(
                        question,
                        results,
                    )

                st.session_state.last_qa = {
                    "question": question,
                    "answer_data": answer_data,
                    "results": results,
                }

            except Exception as error:

                st.error(
                    f"Unable to answer the question: {error}"
                )

    last_qa = st.session_state.last_qa

    if last_qa:

        st.subheader("Generated Answer")

        st.write(
            last_qa["answer_data"].get("answer", "")
        )

        st.markdown("### Key Findings")

        for finding in last_qa["answer_data"].get(
            "key_findings", []
        ):

            st.markdown(
                f"- {finding}"
            )

        suggested_actions = last_qa["answer_data"].get(
            "suggested_actions", []
        )

        if suggested_actions:

            st.markdown("### Related Action Items")

            for action in suggested_actions:

                st.markdown(
                    f"- {action}"
                )

        results = last_qa.get("results", [])

        if results:

            st.subheader("Retrieved Information")

            for number, result in enumerate(
                results,
                start=1
            ):

                st.markdown(
                    f"**Relevant Excerpt {number}**"
                )

                st.write(
                    result["chunk"]
                )

                st.caption(
                    f"Similarity score: {result['score']:.3f}"
                )

        else:

            st.warning(
                "No relevant information was found."
            )

else:

    st.info(
        "Upload and process project documents to use the assistant."
    )
