import re
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from collections import deque
from datetime import datetime

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st
from pypdf import PdfReader

from requirements import extract_requirements
from parser import (
    parse_requirements,
    infer_final_states,
)
from fsm import FiniteStateMachine
from consistency import check_consistency


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ReqVerify AI",
    page_icon="🔍",
    layout="wide",
)


# =========================================================
# DOCUMENT READING
# =========================================================

def read_docx(file_bytes):

    """
    Extract paragraphs and table cells from DOCX
    without requiring an additional DOCX library.
    """

    text_parts = []

    with ZipFile(
        BytesIO(file_bytes)
    ) as archive:

        xml_data = archive.read(
            "word/document.xml"
        )

    root = ET.fromstring(
        xml_data
    )

    namespace = {
        "w":
            "http://schemas.openxmlformats.org/"
            "wordprocessingml/2006/main"
    }

    # Paragraphs.
    for paragraph in root.findall(
        ".//w:p",
        namespace
    ):

        words = []

        for node in paragraph.findall(
            ".//w:t",
            namespace
        ):

            if node.text:
                words.append(
                    node.text
                )

        line = " ".join(words).strip()

        if line:
            text_parts.append(line)

    # Tables.
    for table in root.findall(
        ".//w:tbl",
        namespace
    ):

        for row in table.findall(
            "./w:tr",
            namespace
        ):

            cells = []

            for cell in row.findall(
                "./w:tc",
                namespace
            ):

                cell_text = " ".join(
                    node.text
                    for node in cell.findall(
                        ".//w:t",
                        namespace
                    )
                    if node.text
                )

                cell_text = (
                    re.sub(
                        r"\s+",
                        " ",
                        cell_text
                    )
                    .strip()
                )

                if cell_text:
                    cells.append(
                        cell_text
                    )

            if cells:

                text_parts.append(
                    " | ".join(cells)
                )

    return "\n".join(
        text_parts
    )


def read_uploaded_file(uploaded_file):

    filename = (
        uploaded_file.name.lower()
    )

    data = uploaded_file.read()

    # ------------------------------------------------------
    # PDF
    # ------------------------------------------------------

    if filename.endswith(".pdf"):

        reader = PdfReader(
            BytesIO(data)
        )

        pages = []

        for page in reader.pages:

            page_text = (
                page.extract_text()
            )

            if page_text:

                pages.append(
                    page_text
                )

        return "\n".join(
            pages
        )

    # ------------------------------------------------------
    # DOCX
    # ------------------------------------------------------

    if filename.endswith(".docx"):

        return read_docx(
            data
        )

    # ------------------------------------------------------
    # TXT / MD / CSV-like text
    # ------------------------------------------------------

    return data.decode(
        "utf-8",
        errors="ignore"
    )


# =========================================================
# TRACEABILITY
# =========================================================

def build_workflow(extracted_requirements):
    """
    Build a domain-independent workflow from extracted requirements.

    The workflow is produced by the generic parser. No shopping,
    hospital, payment, login, or other domain-specific states are
    hardcoded here.
    """
    transitions = parse_requirements(extracted_requirements)

    traceability = []

    functional_requirements = [
        requirement
        for requirement in extracted_requirements
        if requirement.get("type") != "Non-Functional"
    ]

    for index, requirement in enumerate(functional_requirements):

        requirement_id = requirement.get(
            "id",
            f"FR{index + 1}"
        )

        description = requirement.get(
            "description",
            ""
        )

        if index < len(transitions):
            source, event, target = transitions[index]
        else:
            source, event, target = "", "", ""

        traceability.append({
            "id": requirement_id,
            "title": requirement.get("title", ""),
            "description": description,
            "transition": (
                source,
                event,
                target
            ) if source else None,
            "status": (
                "Mapped to FSM"
                if source
                else "Not converted to FSM"
            ),
        })

    return (
        transitions,
        traceability
    )


# =========================================================
# SEQUENCE UTILITIES
# =========================================================

def get_valid_sequence(fsm):

    if (
        fsm.start_state is None
        or not fsm.final_states
    ):

        return []

    queue = deque()

    queue.append(
        (
            fsm.start_state,
            []
        )
    )

    visited = {
        fsm.start_state
    }

    while queue:

        state, events = (
            queue.popleft()
        )

        if state in fsm.final_states:

            return events

        for event, next_state in (
            fsm.transitions.get(
                state,
                []
            )
        ):

            if next_state not in visited:

                visited.add(
                    next_state
                )

                queue.append(
                    (
                        next_state,
                        events + [event]
                    )
                )

    return []


def get_sequence_trace(
    fsm,
    events
):

    states = []

    transitions = []

    if fsm.start_state is None:

        return states, transitions

    current = (
        fsm.start_state
    )

    states.append(
        current
    )

    for event in events:

        found = False

        for transition_event, next_state in (
            fsm.transitions.get(
                current,
                []
            )
        ):

            if (
                transition_event
                == event
            ):

                transitions.append(
                    (
                        current,
                        event,
                        next_state,
                    )
                )

                current = next_state

                states.append(
                    current
                )

                found = True

                break

        if not found:

            break

    return (
        states,
        transitions
    )


# =========================================================
# VISUALIZATION
# =========================================================

def draw_fsm(fsm):

    graph = nx.DiGraph()

    for state in fsm.states:

        graph.add_node(
            state
        )

    for source in fsm.transitions:

        for event, target in (
            fsm.transitions[source]
        ):

            graph.add_edge(
                source,
                target,
                label=event
            )

    if not graph.nodes:

        st.info(
            "No states available."
        )

        return

    figure, axis = plt.subplots(
        figsize=(
            14,
            max(
                6,
                len(graph.nodes) * 0.6
            )
        )
    )

    positions = nx.spring_layout(
        graph,
        seed=42,
        k=1.8,
    )

    nx.draw_networkx_nodes(
        graph,
        positions,
        node_size=2500,
        ax=axis,
    )

    nx.draw_networkx_labels(
        graph,
        positions,
        font_size=9,
        ax=axis,
    )

    nx.draw_networkx_edges(
        graph,
        positions,
        arrows=True,
        arrowsize=20,
        ax=axis,
    )

    labels = nx.get_edge_attributes(
        graph,
        "label"
    )

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=labels,
        font_size=8,
        ax=axis,
    )

    axis.set_title(
        "Generated Finite State Machine"
    )

    axis.axis("off")

    st.pyplot(
        figure,
        clear_figure=True
    )


# =========================================================
# REPORT
# =========================================================

def build_report(
    extracted_requirements,
    fsm,
    unreachable,
    dead_ends,
    consistency_issues,
    traceability,
):

    lines = []

    lines.append(
        "ReqVerify AI - Verification Report"
    )

    lines.append(
        "=" * 50
    )

    lines.append(
        f"Generated: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append("")

    lines.append(
        "REQUIREMENTS"
    )

    lines.append(
        "-" * 50
    )

    for requirement in (
        extracted_requirements
    ):

        lines.append(
            f"{requirement['id']} | "
            f"{requirement['type']} | "
            f"{requirement['title']}"
        )

        lines.append(
            f"  {requirement['description']}"
        )

    lines.append("")

    lines.append(
        "FSM"
    )

    lines.append(
        "-" * 50
    )

    lines.append(
        f"States: {len(fsm.states)}"
    )

    lines.append(
        f"Transitions: "
        f"{fsm.get_transition_count()}"
    )

    lines.append(
        f"Start state: "
        f"{fsm.start_state}"
    )

    lines.append(
        f"Final states: "
        f"{', '.join(sorted(fsm.final_states))}"
    )

    lines.append("")

    for source in sorted(
        fsm.transitions
    ):

        for event, target in (
            fsm.transitions[source]
        ):

            lines.append(
                f"{source} "
                f"--{event}--> "
                f"{target}"
            )

    lines.append("")

    lines.append(
        "VERIFICATION"
    )

    lines.append(
        "-" * 50
    )

    lines.append(
        f"Unreachable states: "
        f"{len(unreachable)}"
    )

    for state in sorted(
        unreachable
    ):

        lines.append(
            f"  - {state}"
        )

    lines.append(
        f"Dead-end states: "
        f"{len(dead_ends)}"
    )

    for state in sorted(
        dead_ends
    ):

        lines.append(
            f"  - {state}"
        )

    lines.append(
        f"Consistency issues: "
        f"{len(consistency_issues)}"
    )

    for issue in consistency_issues:

        lines.append(
            f"  - {issue['message']}"
        )

    return "\n".join(
        lines
    )


# =========================================================
# PAGE
# =========================================================

st.title(
    "🔍 ReqVerify AI"
)

st.subheader(
    "Intelligent Software Requirement "
    "Consistency and Workflow Verification"
)

st.write(
    "Upload an SRS document or enter requirements. "
    "ReqVerify AI extracts requirements, identifies "
    "workflow relationships, builds a finite state "
    "machine and performs structural verification."
)


# =========================================================
# INPUT
# =========================================================

col1, col2 = st.columns(
    [2, 1]
)

with col1:

    uploaded_file = st.file_uploader(
        "Upload SRS Document",
        type=[
            "pdf",
            "docx",
            "txt",
            "md",
        ],
    )

with col2:

    demo_mode = st.checkbox(
        "Enable verification test case",
        value=False,
    )

    st.caption(
        "Adds generic artificial defects "
        "to demonstrate verification."
    )


default_requirements = """1. User Login
The user logs in to the system.

2. Dashboard
After successful login, the dashboard is displayed.

3. Shopping Cart
The user can add products to the cart.

4. Payment
The user proceeds to payment.

5. Order Confirmation
If payment succeeds, the order is confirmed.

6. Payment Failure
If payment fails, the user can retry payment.
"""


if uploaded_file is not None:

    try:

        uploaded_text = (
            read_uploaded_file(
                uploaded_file
            )
        )

    except Exception as error:

        st.error(
            "Unable to read the uploaded "
            f"document: {error}"
        )

        st.stop()

else:

    uploaded_text = (
        default_requirements
    )


requirements_text = st.text_area(
    "SRS Content",
    value=uploaded_text,
    height=260,
)


# =========================================================
# ANALYZE
# =========================================================

if st.button(
    "🔍 Analyze Requirements",
    type="primary",
):

    # ------------------------------------------------------
    # 1. REQUIREMENT EXTRACTION
    # ------------------------------------------------------

    extracted_requirements = (
        extract_requirements(
            requirements_text
        )
    )

    if not extracted_requirements:

        st.error(
            "No requirements could be extracted."
        )

        st.stop()

    st.header(
        "1. Extracted Requirements"
    )

    for requirement in (
        extracted_requirements
    ):

        badge = (
            "Functional"
            if requirement["type"]
            == "Functional"
            else "Non-Functional"
        )

        with st.expander(
            f"{requirement['id']} — "
            f"{requirement['title']} "
            f"({badge})"
        ):

            st.write(
                requirement[
                    "description"
                ]
            )

            if requirement[
                "action"
            ]:

                st.caption(
                    "Action: "
                    + requirement[
                        "action"
                    ]
                )

            if requirement[
                "condition"
            ]:

                st.caption(
                    "Condition: "
                    + requirement[
                        "condition"
                    ]
                )

            if requirement[
                "outcome"
            ]:

                st.caption(
                    "Outcome: "
                    + requirement[
                        "outcome"
                    ]
                )

    # ------------------------------------------------------
    # 2. WORKFLOW
    # ------------------------------------------------------

    (
        transitions,
        traceability
    ) = build_workflow(
        extracted_requirements
    )

    if not transitions:

        st.warning(
            "Requirements were extracted, "
            "but no workflow-oriented "
            "functional relationships "
            "could be converted into an FSM."
        )

        st.stop()

    # ------------------------------------------------------
    # 3. FSM
    # ------------------------------------------------------

    fsm = FiniteStateMachine()

    fsm.set_start_state(
        "START"
    )

    for (
        source,
        event,
        target
    ) in transitions:

        fsm.add_transition(
            source,
            event,
            target
        )

    # ------------------------------------------------------
    # 4. FINAL STATES
    # ------------------------------------------------------

    final_states = (
        infer_final_states(
            extracted_requirements,
            transitions,
        )
    )

    for state in final_states:

        fsm.add_final_state(
            state
        )

    # ------------------------------------------------------
    # 5. DEMONSTRATION DEFECTS
    # ------------------------------------------------------

    if demo_mode:

        # Generic unreachable state.
        fsm.add_state(
            "VERIFICATION_UNREACHABLE"
        )

        # Choose a reachable state to attach
        # an artificial dead-end branch.
        reachable_states = (
            fsm.get_reachable_states()
        )

        candidate = None

        for state in reachable_states:

            if (
                state not in fsm.final_states
            ):

                candidate = state
                break

        if candidate is None:

            candidate = (
                fsm.start_state
            )

        fsm.add_transition(
            candidate,
            "verification_test",
            "VERIFICATION_DEAD_END",
        )

    # ------------------------------------------------------
    # 6. VERIFICATION
    # ------------------------------------------------------

    reachable = (
        fsm.get_reachable_states()
    )

    unreachable = (
        fsm.get_unreachable_states()
    )

    dead_ends = (
        fsm.get_dead_end_states()
    )

    consistency_issues = (
        check_consistency(
            extracted_requirements
        )
    )

    # ------------------------------------------------------
    # 7. METRICS
    # ------------------------------------------------------

    st.header(
        "2. FSM Summary"
    )

    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )

    metric1.metric(
        "Requirements",
        len(extracted_requirements),
    )

    metric2.metric(
        "States",
        len(fsm.states),
    )

    metric3.metric(
        "Transitions",
        fsm.get_transition_count(),
    )

    metric4.metric(
        "Verification Issues",
        (
            len(unreachable)
            + len(dead_ends)
            + len(consistency_issues)
        ),
    )

    # ------------------------------------------------------
    # 8. TRANSITIONS
    # ------------------------------------------------------

    st.subheader(
        "Generated Workflow"
    )

    for (
        source,
        event,
        target
    ) in transitions:

        st.write(
            f"**{source}** "
            f"→ `{event}` → "
            f"**{target}**"
        )

    # ------------------------------------------------------
    # 9. TRACEABILITY
    # ------------------------------------------------------

    st.subheader(
        "Requirement → FSM Traceability"
    )

    for item in traceability:

        if item["transition"]:

            source, event, target = (
                item["transition"]
            )

            st.write(
                f"**{item['id']} — "
                f"{item['title']}**  "
                f"→ `{source} --{event}--> {target}`"
            )

        else:

            st.write(
                f"**{item['id']} — "
                f"{item['title']}**  "
                f"→ {item['status']}"
            )

    # ------------------------------------------------------
    # 10. FORMAL VERIFICATION
    # ------------------------------------------------------

    st.header(
        "3. Formal Verification"
    )

    if not unreachable:

        st.success(
            "✓ No unreachable states detected."
        )

    else:

        st.error(
            "✗ Unreachable states detected."
        )

        for state in sorted(
            unreachable
        ):

            st.write(
                f"- `{state}` cannot be "
                "reached from START."
            )

    if not dead_ends:

        st.success(
            "✓ No non-final dead-end states detected."
        )

    else:

        st.error(
            "✗ Dead-end states detected."
        )

        for state in sorted(
            dead_ends
        ):

            st.write(
                f"- `{state}` has no outgoing "
                "transition and is not final."
            )

    if not consistency_issues:

        st.success(
            "✓ No potential contradictions "
            "detected by the consistency rules."
        )

    else:

        st.warning(
            "Potential requirement contradictions "
            "were detected."
        )

        for issue in (
            consistency_issues
        ):

            st.write(
                f"- {issue['message']}"
            )

    # ------------------------------------------------------
    # 11. RECOMMENDATIONS
    # ------------------------------------------------------

    st.header(
        "4. Recommendations"
    )

    recommendations = []

    for state in sorted(
        unreachable
    ):

        recommendations.append(
            f"Review state '{state}'. "
            "It cannot be reached from START. "
            "Add an appropriate transition or "
            "remove it if it is not part of the "
            "intended workflow."
        )

    for state in sorted(
        dead_ends
    ):

        recommendations.append(
            f"Review state '{state}'. "
            "It is reachable but has no outgoing "
            "transition and is not marked final."
        )

    for issue in (
        consistency_issues
    ):

        recommendations.append(
            issue["message"]
        )

    if not recommendations:

        st.success(
            "No corrective recommendations are required."
        )

    else:

        for recommendation in (
            recommendations
        ):

            st.write(
                "• " + recommendation
            )

    # ------------------------------------------------------
    # 12. FSM VISUALIZATION
    # ------------------------------------------------------

    st.header(
        "5. FSM Visualization"
    )

    draw_fsm(
        fsm
    )

    # ------------------------------------------------------
    # 13. SEQUENCE VALIDATION
    # ------------------------------------------------------

    st.header(
        "6. Sequence Validation"
    )

    valid_sequence = (
        get_valid_sequence(
            fsm
        )
    )

    if valid_sequence:

        st.write(
            "Generated valid event sequence:"
        )

        st.code(
            " → ".join(
                valid_sequence
            )
        )

        is_valid = (
            fsm.check_sequence(
                valid_sequence
            )
        )

        if is_valid:

            st.success(
                "✓ Sequence accepted by the FSM."
            )

        else:

            st.error(
                "✗ Generated sequence was rejected."
            )

    else:

        st.info(
            "No complete path from START "
            "to a final state was found."
        )

    # ------------------------------------------------------
    # 14. DOWNLOAD REPORT
    # ------------------------------------------------------

    st.header(
        "7. Verification Report"
    )

    report = build_report(
        extracted_requirements,
        fsm,
        unreachable,
        dead_ends,
        consistency_issues,
        traceability,
    )

    st.download_button(
        "📄 Download Verification Report",
        data=report,
        file_name="ReqVerifyAI_Verification_Report.txt",
        mime="text/plain",
    )