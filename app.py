import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from pypdf import PdfReader
from datetime import datetime

from parser import parse_requirements
from fsm import FiniteStateMachine
from consistency import check_consistency
from requirements import extract_requirements


def get_sequence_trace(fsm, events):
    """Return states and transitions visited while executing an event sequence."""

    if fsm.start_state is None:
        return [], []

    states = [fsm.start_state]
    visited_transitions = []
    current_state = fsm.start_state

    for event in events:
        found = False

        for transition_event, next_state in fsm.transitions.get(
            current_state, []
        ):
            if transition_event == event:
                visited_transitions.append(
                    (current_state, event, next_state)
                )
                current_state = next_state
                states.append(current_state)
                found = True
                break

        if not found:
            break

    return states, visited_transitions

def build_requirement_traceability(
    extracted_requirements,
    transitions
):
    """Map each functional requirement to only the FSM transitions
    that are directly represented by that requirement."""

    traceability = []

    for index, requirement in enumerate(
        extracted_requirements,
        start=1
    ):
        description = requirement["description"]
        text = description.lower().strip()
        matched_transitions = []

        for from_state, event, to_state in transitions:
            match = False

            # FR describing the login action itself.
            if event == "login":
                match = any(phrase in text for phrase in [
                    "user logs in",
                    "user login",
                    "logs in",
                    "signs in",
                    "user signs in",
                    "authenticate",
                    "user authenticates"
                ])

            # Successful login leads to the dashboard.
            elif event == "success" and to_state == "DASHBOARD":
                match = (
                    ("successful login" in text or
                     "successful authentication" in text or
                     "after login" in text or
                     "after successful login" in text)
                    and "dashboard" in text
                )

            # Adding an item/product to the cart.
            elif event == "add_item":
                match = (
                    ("add" in text and "cart" in text)
                    or "add product" in text
                    or "add item" in text
                )

            # Moving from cart to payment/checkout.
            elif event == "checkout":
                match = (
                    "proceeds to payment" in text
                    or "proceed to payment" in text
                    or "proceeds for payment" in text
                    or "checkout" in text
                    or "checks out" in text
                )

            # Successful payment confirms the order.
            elif event == "success" and to_state == "ORDER_CONFIRMED":
                match = (
                    "payment succeeds" in text
                    or "payment is successful" in text
                    or "successful payment" in text
                    or ("payment" in text and "order is confirmed" in text)
                    or ("payment" in text and "order confirmed" in text)
                )

            # Failed payment moves to retry.
            elif event == "failure":
                match = (
                    "payment fails" in text
                    or "payment failed" in text
                    or "payment failure" in text
                    or "payment unsuccessful" in text
                )

            # Retry transition.
            elif event == "retry":
                match = (
                    "retry payment" in text
                    or "retry" in text
                    or "try again" in text
                )

            # Optional cancellation transition.
            elif event == "cancel":
                match = (
                    "cancel payment" in text
                    or "payment is cancelled" in text
                    or "payment is canceled" in text
                    or "order is cancelled" in text
                    or "order is canceled" in text
                )

            if match:
                transition_text = (
                    f"{from_state} --{event}--> {to_state}"
                )
                if transition_text not in matched_transitions:
                    matched_transitions.append(transition_text)

        traceability.append({
            "id": f"FR{index}",
            "requirement": description,
            "transitions": matched_transitions
        })

    return traceability

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ReqVerify AI",
    page_icon="🔍",
    layout="wide"
)


# =========================================================
# CUSTOM UI
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #666666;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🔍 ReqVerify AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Intelligent Software Requirement Consistency '
    'and Workflow Verification System'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "ReqVerify AI analyzes software requirements, "
    "extracts workflows, models them as Finite State "
    "Machines and performs formal verification."
)


# =========================================================
# INPUT
# =========================================================

st.header("Software Requirement Input")

demo_mode = st.checkbox(
    "Enable verification test case",
    value=False
)

st.caption(
    "This option intentionally introduces workflow defects "
    "to demonstrate the verification capabilities."
)


default_requirements = """User logs in.
After successful login, dashboard is displayed.
User can add products to cart.
User proceeds to payment.
If payment succeeds, order is confirmed.
If payment fails, user can retry payment."""


uploaded_file = st.file_uploader(
    "Upload SRS Document",
    type=["txt", "pdf"]
)


if uploaded_file is not None:

    if uploaded_file.name.lower().endswith(".pdf"):

        reader = PdfReader(uploaded_file)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        uploaded_text = "\n".join(pages)

    else:

        uploaded_text = uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )

    requirements = st.text_area(
        "Extracted SRS Content",
        value=uploaded_text,
        height=250
    )

else:

    requirements = st.text_area(
        "Enter Software Requirements",
        height=220,
        value=default_requirements
    )


# =========================================================
# ANALYSIS
# =========================================================

if st.button(
    "🔍 Analyze Requirements",
    type="primary"
):

    # =====================================================
    # 1. REQUIREMENT EXTRACTION
    # =====================================================

    extracted_requirements = extract_requirements(
        requirements
    )


    # =====================================================
    # 2. WORKFLOW PARSING
    # =====================================================

    transitions = parse_requirements(
        requirements
    )


    if not transitions:

        st.error(
            "No workflow could be extracted from "
            "the supplied requirements."
        )

        st.stop()


    # =====================================================
    # 3. FSM CONSTRUCTION
    # =====================================================

    fsm = FiniteStateMachine()

    fsm.set_start_state("START")


    for from_state, event, to_state in transitions:

        fsm.add_transition(
            from_state,
            event,
            to_state
        )


    # =====================================================
    # 4. FINAL STATE
    # =====================================================

    if "ORDER_CONFIRMED" in fsm.states:

        fsm.add_final_state(
            "ORDER_CONFIRMED"
        )

    if "ORDER_CANCELLED" in fsm.states:

        fsm.add_final_state(
            "ORDER_CANCELLED"
        )


    # =====================================================
    # 5. FAULT INJECTION FOR DEMONSTRATION
    # =====================================================

    if demo_mode:

        # Intentionally unreachable state
        fsm.add_state(
            "REFUND_APPROVED"
        )

        # Intentionally reachable dead-end state
        fsm.add_transition(
            "PAYMENT",
            "processing",
            "PROCESSING"
        )


    # =====================================================
    # IMPORTANT:
    # BUILD ACTUAL FSM TRANSITION LIST
    # =====================================================

    actual_transitions = []

    for from_state in fsm.transitions:

        for event, to_state in fsm.transitions[
            from_state
        ]:

            actual_transitions.append(
                (
                    from_state,
                    event,
                    to_state
                )
            )
            
    traceability = build_requirement_traceability(
        extracted_requirements,
        actual_transitions
    )


    # =====================================================
    # 6. FORMAL VERIFICATION
    # =====================================================

    reachable = (
        fsm.get_reachable_states()
    )

    unreachable = (
        fsm.get_unreachable_states()
    )

    dead_ends = (
        fsm.get_dead_end_states()
    )


    # =====================================================
    # 7. CONSISTENCY CHECK
    # =====================================================

    consistency_issues = (
        check_consistency(
            requirements
        )
    )


    # =====================================================
    # 8. ISSUE COUNT
    # =====================================================

    total_issues = (
        len(unreachable)
        + len(dead_ends)
        + len(consistency_issues)
    )


    # =====================================================
    # 9. RECOMMENDATIONS
    # =====================================================

    recommendations = []


    for state in sorted(unreachable):

        recommendations.append(
            f"Review state '{state}'. "
            "It cannot be reached from the START state. "
            "Add an appropriate transition or remove "
            "the state if it is not part of the intended workflow."
        )


    for state in sorted(dead_ends):

        if state in fsm.final_states:
            continue

        recommendations.append(
            f"Review state '{state}'. "
            "It is a dead-end state without an outgoing "
            "transition. Define the next valid workflow transition."
        )


    for issue in consistency_issues:

        recommendations.append(
            "Resolve the conflicting requirements: "
            + issue
        )


    # =====================================================
    # 10. AUTOMATIC SEQUENCE TESTS
    # =====================================================

    test_cases = [

        (
            "Valid Login-to-Order Flow",
            [
                "login",
                "success",
                "add_item",
                "checkout",
                "success"
            ],
            True
        ),

        (
            "Valid Payment Retry Flow",
            [
                "login",
                "success",
                "add_item",
                "checkout",
                "failure",
                "retry",
                "success"
            ],
            True
        ),

        (
            "Payment Cancellation Not Defined",
            [
                "login",
                "success",
                "add_item",
                "checkout",
                "cancel"
            ],
            False
        ),

        (
            "Invalid Checkout Before Login",
            [
                "checkout"
            ],
            False
        ),

        (
            "Invalid Payment Before Cart",
            [
                "login",
                "success",
                "checkout"
            ],
            False
        ),

        (
            "Invalid Unknown Event",
            [
                "login",
                "logout"
            ],
            False
        )

    ]


    sequence_results = []


    for test_name, events, expected_valid in test_cases:

        is_valid, message = (
            fsm.check_sequence(
                events
            )
        )

        sequence_results.append(
            {
                "name": test_name,
                "sequence": ", ".join(events),
                "result": (
                    "Accepted"
                    if is_valid
                    else "Rejected"
                ),
                "expected": (
                    "Accepted"
                    if expected_valid
                    else "Rejected"
                ),
                "message": message,
                "valid": is_valid,
                "expected_valid": expected_valid,
                "test_passed": is_valid == expected_valid
            }
        )


    accepted_count = sum(
        1
        for result in sequence_results
        if result["valid"]
    )


    rejected_count = (
        len(sequence_results)
        - accepted_count
    )


    validation_passed_count = sum(
        1
        for result in sequence_results
        if result["test_passed"]
    )

    validation_failed_count = (
        len(sequence_results)
        - validation_passed_count
    )

    validation_rate = (
        (validation_passed_count / len(sequence_results)) * 100
        if sequence_results
        else 0.0
    )

    covered_states = set()
    covered_transitions = set()

    for result in sequence_results:
        events = [
            event.strip()
            for event in result["sequence"].split(",")
            if event.strip()
        ]
        states_seen, transitions_seen = get_sequence_trace(
            fsm,
            events
        )
        covered_states.update(states_seen)
        covered_transitions.update(transitions_seen)

    reachable_state_count = len(reachable)
    state_coverage = (
        (len(covered_states & reachable) / reachable_state_count) * 100
        if reachable_state_count
        else 0.0
    )

    transition_count = len(actual_transitions)
    transition_coverage = (
        (len(covered_transitions & set(actual_transitions)) / transition_count) * 100
        if transition_count
        else 0.0
    )


    # =====================================================
    # 11. STORE RESULTS
    # =====================================================

    st.session_state["fsm"] = fsm

    st.session_state["transitions"] = (
        actual_transitions
    )

    st.session_state["requirements"] = (
        requirements
    )

    st.session_state["extracted_requirements"] = (
        extracted_requirements
    )

    st.session_state["traceability"] = (
        traceability
    )

    st.session_state["reachable"] = (
        reachable
    )

    st.session_state["unreachable"] = (
        unreachable
    )

    st.session_state["dead_ends"] = (
        dead_ends
    )

    st.session_state["consistency_issues"] = (
        consistency_issues
    )

    st.session_state["recommendations"] = (
        recommendations
    )

    st.session_state["total_issues"] = (
        total_issues
    )

    st.session_state["sequence_results"] = (
        sequence_results
    )

    st.session_state["accepted_count"] = (
        accepted_count
    )

    st.session_state["rejected_count"] = (
        rejected_count
    )

    st.session_state["validation_passed_count"] = (
        validation_passed_count
    )

    st.session_state["validation_failed_count"] = (
        validation_failed_count
    )

    st.session_state["validation_rate"] = (
        validation_rate
    )

    st.session_state["covered_states"] = (
        covered_states
    )

    st.session_state["covered_transitions"] = (
        covered_transitions
    )

    st.session_state["state_coverage"] = (
        state_coverage
    )

    st.session_state["transition_coverage"] = (
        transition_coverage
    )

    st.session_state["analyzed"] = True


    # =====================================================
    # 12. GENERATE REPORT
    # =====================================================

    report_lines = []

    report_lines.append(
        "REQVERIFY AI"
    )

    report_lines.append(
        "Intelligent Software Requirement Consistency "
        "and Workflow Verification System"
    )

    report_lines.append(
        "=" * 70
    )

    report_lines.append("")

    report_lines.append(
        "Analysis Date: "
        + datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    )

    report_lines.append("")


    report_lines.append(
        "1. INPUT SOFTWARE REQUIREMENTS"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        requirements
    )

    report_lines.append("")


    report_lines.append(
        "2. EXTRACTED FUNCTIONAL REQUIREMENTS"
    )

    report_lines.append(
        "-" * 70
    )

    for index, requirement in enumerate(
        extracted_requirements,
        start=1
    ):

        report_lines.append(
            f"FR{index}: "
            + requirement["description"]
        )

    report_lines.append("")


    report_lines.append(
        "3. REQUIREMENT TO FSM TRACEABILITY"
    )

    report_lines.append(
        "-" * 70
    )

    for item in traceability:

        report_lines.append(
            f"{item['id']}: {item['requirement']}"
        )

        if item["transitions"]:
            for transition in item["transitions"]:
                report_lines.append(
                    "  " + transition
                )
        else:
            report_lines.append(
                "  No direct FSM transition mapped."
            )

    report_lines.append("")


    report_lines.append(
        "4. EXTRACTED FSM WORKFLOW"
    )

    report_lines.append(
        "-" * 70
    )

    for from_state, event, to_state in actual_transitions:

        report_lines.append(
            f"{from_state} --{event}--> {to_state}"
        )

    report_lines.append("")


    report_lines.append(
        "5. FSM STATE INFORMATION"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        "All States: "
        + ", ".join(
            sorted(fsm.states)
        )
    )

    report_lines.append(
        "Reachable States: "
        + ", ".join(
            sorted(reachable)
        )
    )

    report_lines.append(
        "Unreachable States: "
        + (
            ", ".join(
                sorted(unreachable)
            )
            if unreachable
            else "None"
        )
    )

    report_lines.append(
        "Dead-end States: "
        + (
            ", ".join(
                sorted(dead_ends)
            )
            if dead_ends
            else "None"
        )
    )

    report_lines.append("")


    report_lines.append(
        "6. REQUIREMENT CONSISTENCY"
    )

    report_lines.append(
        "-" * 70
    )

    if consistency_issues:

        for issue in consistency_issues:

            report_lines.append(
                "ISSUE: " + issue
            )

    else:

        report_lines.append(
            "No contradictions detected."
        )

    report_lines.append("")


    report_lines.append(
        "7. AUTOMATIC SEQUENCE TEST RESULTS"
    )

    report_lines.append(
        "-" * 70
    )

    for result in sequence_results:

        report_lines.append(
            f"Test: {result['name']}"
        )

        report_lines.append(
            f"Sequence: {result['sequence']}"
        )

        report_lines.append(
            f"Result: {result['result']}"
        )

        report_lines.append(
            f"Explanation: {result['message']}"
        )

        report_lines.append("")


    report_lines.append(
        "8. EXPERIMENTAL VALIDATION RESULTS"
    )

    report_lines.append(
        "-" * 70
    )

    report_lines.append(
        f"Total Test Cases: {len(sequence_results)}"
    )

    report_lines.append(
        f"Validation Tests Passed: {validation_passed_count}"
    )

    report_lines.append(
        f"Validation Tests Failed: {validation_failed_count}"
    )

    report_lines.append(
        f"Test Suite Agreement: {validation_rate:.1f}%"
    )

    report_lines.append(
        f"FSM State Coverage: {state_coverage:.1f}%"
    )

    report_lines.append(
        f"FSM Transition Coverage: {transition_coverage:.1f}%"
    )

    report_lines.append("")

    for result in sequence_results:
        report_lines.append(
            f"{result['name']}: Expected={result['expected']}, "
            f"Actual={result['result']}, "
            f"Validation={'PASS' if result['test_passed'] else 'FAIL'}"
        )

    report_lines.append("")


    report_lines.append(
        "9. OVERALL VERIFICATION RESULT"
    )

    report_lines.append(
        "-" * 70
    )

    if total_issues == 0:

        report_lines.append(
            "VERIFICATION PASSED"
        )

    else:

        report_lines.append(
            f"VERIFICATION ISSUES DETECTED: "
            f"{total_issues}"
        )

    report_lines.append("")


    report_lines.append(
        "10. EXPLAINABLE RECOMMENDATIONS"
    )

    report_lines.append(
        "-" * 70
    )

    if recommendations:

        for index, recommendation in enumerate(
            recommendations,
            start=1
        ):

            report_lines.append(
                f"{index}. {recommendation}"
            )

    else:

        report_lines.append(
            "No corrective recommendations required."
        )

    report_lines.append("")

    report_lines.append(
        "=" * 70
    )

    report_lines.append(
        "Generated by ReqVerify AI"
    )


    st.session_state["verification_report"] = (
        "\n".join(report_lines)
    )


# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.get(
    "analyzed",
    False
):

    fsm = st.session_state["fsm"]

    transitions = st.session_state[
        "transitions"
    ]

    extracted_requirements = (
        st.session_state[
            "extracted_requirements"
        ]
    )

    traceability = st.session_state["traceability"]

    reachable = st.session_state[
        "reachable"
    ]

    unreachable = st.session_state[
        "unreachable"
    ]

    dead_ends = st.session_state[
        "dead_ends"
    ]

    consistency_issues = (
        st.session_state[
            "consistency_issues"
        ]
    )

    recommendations = (
        st.session_state[
            "recommendations"
        ]
    )

    total_issues = (
        st.session_state[
            "total_issues"
        ]
    )

    sequence_results = (
        st.session_state[
            "sequence_results"
        ]
    )

    accepted_count = (
        st.session_state[
            "accepted_count"
        ]
    )

    rejected_count = (
        st.session_state[
            "rejected_count"
        ]
    )

    verification_report = (
        st.session_state[
            "verification_report"
        ]
    )


    # =====================================================
    # DASHBOARD
    # =====================================================

    st.divider()

    st.header(
        "📊 Verification Dashboard"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Functional Requirements",
            len(extracted_requirements)
        )


    with col2:

        st.metric(
            "FSM States",
            len(fsm.states)
        )


    with col3:

        st.metric(
            "FSM Transitions",
            len(transitions)
        )


    with col4:

        st.metric(
            "Verification Issues",
            total_issues
        )


    if total_issues == 0:

        st.success(
            "🟢 SYSTEM STATUS: VERIFICATION PASSED"
        )

    else:

        st.error(
            "🔴 SYSTEM STATUS: ISSUES DETECTED"
        )

    # -----------------------------------------------------
    # VERIFICATION MODE INDICATOR
    # -----------------------------------------------------

    if demo_mode:

        st.warning(
            "🧪 VERIFICATION TEST MODE ACTIVE — "
            "Artificial workflow defects have been injected "
            "to demonstrate formal verification."
        )

    else:

        st.info(
            "✅ NORMAL VERIFICATION MODE — "
            "The FSM is generated directly from the supplied requirements."
        )


    # =====================================================
    # EXTRACTED REQUIREMENTS
    # =====================================================

    st.header(
        "1. Extracted Functional Requirements"
    )


    if extracted_requirements:

        for index, requirement in enumerate(
            extracted_requirements,
            start=1
        ):

            with st.expander(
                f"FR{index} — "
                f"{requirement['type']}"
            ):

                st.write(
                    requirement["description"]
                )

    else:

        st.warning(
            "No functional requirements identified."
        )


    # =====================================================
    # REQUIREMENT → FSM TRACEABILITY
    # =====================================================

    st.header(
        "2. Requirement → FSM Traceability"
    )

    st.write(
        "This mapping shows how each extracted functional requirement "
        "contributes to the generated FSM workflow."
    )

    for item in st.session_state["traceability"]:

        st.write(
            f"**{item['id']} — {item['requirement']}**"
        )

        if item["transitions"]:

            st.write("**Generated FSM transition(s):**")

            for transition in item["transitions"]:

                st.code(transition)

        else:

            st.caption(
                "No direct FSM transition mapped to this requirement."
            )


    # =====================================================
    # WORKFLOW
    # =====================================================

    st.header(
        "3. Extracted Workflow"
    )


    for from_state, event, to_state in transitions:

        st.write(
            f"**{from_state}** "
            f"── `{event}` ──> "
            f"**{to_state}**"
        )


    # =====================================================
    # FORMAL VERIFICATION
    # =====================================================

    st.header(
        "4. Formal Verification Results"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Total States",
            len(fsm.states)
        )


    with col2:

        st.metric(
            "Reachable",
            len(reachable)
        )


    with col3:

        st.metric(
            "Unreachable",
            len(unreachable)
        )


    with col4:

        st.metric(
            "Dead-end",
            len(dead_ends)
        )


    if unreachable:

        st.error(
            "⚠ Unreachable States: "
            + ", ".join(
                sorted(unreachable)
            )
        )

    else:

        st.success(
            "✓ All states are reachable from START."
        )


    if dead_ends:

        st.warning(
            "⚠ Dead-end States: "
            + ", ".join(
                sorted(dead_ends)
            )
        )

    else:

        st.success(
            "✓ No dead-end states detected."
        )


    # =====================================================
    # CONSISTENCY
    # =====================================================

    st.header(
        "5. Requirement Consistency"
    )


    if consistency_issues:

        st.error(
            "⚠ Requirement inconsistencies detected."
        )

        for issue in consistency_issues:

            st.warning(
                issue
            )

    else:

        st.success(
            "✓ No contradictions detected "
            "in the supported consistency checks."
        )


    # =====================================================
    # OVERALL RESULT
    # =====================================================

    st.header(
        "Overall Verification Result"
    )


    if total_issues == 0:

        st.success(
            "✓ VERIFICATION PASSED — "
            "No structural or consistency issues detected."
        )

    else:

        st.error(
            f"⚠ VERIFICATION ISSUES DETECTED — "
            f"{total_issues} issue(s) found."
        )


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.header(
        "Explainable Recommendations"
    )


    if recommendations:

        for index, recommendation in enumerate(
            recommendations,
            start=1
        ):

            st.info(
                f"Recommendation {index}: "
                f"{recommendation}"
            )

    else:

        st.success(
            "No corrective recommendations are required."
        )


    # =====================================================
    # SEQUENCE VALIDATION
    # =====================================================

    st.header(
        "6. Sequence Validation"
    )

    st.write(
        "A sequence represents a series of events "
        "provided to the generated Finite State Machine."
    )


    # =====================================================
    # MANUAL TEST
    # =====================================================

    st.subheader(
        "Manual Sequence Test"
    )


    sequence_input = st.text_input(
        "Enter events separated by commas",
        value=(
            "login, success, add_item, "
            "checkout, success"
        ),
        key="sequence_input"
    )


    if st.button(
        "Validate Sequence",
        key="validate_sequence"
    ):

        events = [

            event.strip()

            for event in sequence_input.split(",")

            if event.strip()

        ]


        is_valid, message = (
            fsm.check_sequence(
                events
            )
        )


        if is_valid:

            st.success(
                "✓ " + message
            )

        else:

            st.error(
                "✗ " + message
            )


    # =====================================================
    # AUTOMATIC TESTS
    # =====================================================

    st.subheader(
        "Automatic Sequence Test Cases"
    )


    seq_col1, seq_col2 = st.columns(2)


    with seq_col1:

        st.metric(
            "Accepted",
            accepted_count
        )


    with seq_col2:

        st.metric(
            "Rejected",
            rejected_count
        )


    for result in sequence_results:

        if result["valid"]:

            status = "✅ Accepted"

        else:

            status = "❌ Rejected"


        with st.expander(
            f"{status} — {result['name']}"
        ):

            st.write(
                "**Input Sequence:**"
            )

            st.code(
                result["sequence"]
            )

            st.write(
                "**Result:** "
                + result["result"]
            )

            st.write(
                "**Explanation:** "
                + result["message"]
            )


    # =====================================================
    # EXPERIMENTAL VALIDATION DASHBOARD
    # =====================================================

    st.header(
        "7. Experimental Validation Dashboard"
    )

    st.caption(
        "These metrics evaluate whether the implemented FSM behaves as expected "
        "for the predefined validation scenarios. Acceptance/rejection counts "
        "describe test inputs and are not software quality scores."
    )

    val_col1, val_col2, val_col3, val_col4 = st.columns(4)

    with val_col1:
        st.metric(
            "Total Test Cases",
            len(sequence_results)
        )

    with val_col2:
        st.metric(
            "Validation Passed",
            st.session_state["validation_passed_count"]
        )

    with val_col3:
        st.metric(
            "Validation Failed",
            st.session_state["validation_failed_count"]
        )

    with val_col4:
        st.metric(
            "Test Suite Agreement",
            f"{st.session_state['validation_rate']:.1f}%"
        )

    cov_col1, cov_col2 = st.columns(2)

    with cov_col1:
        st.metric(
            "FSM State Coverage",
            f"{st.session_state['state_coverage']:.1f}%"
        )

    with cov_col2:
        st.metric(
            "FSM Transition Coverage",
            f"{st.session_state['transition_coverage']:.1f}%"
        )

    validation_table = []

    for result in sequence_results:
        validation_table.append(
            {
                "Test Case": result["name"],
                "Expected": result["expected"],
                "Actual": result["result"],
                "Validation": (
                    "PASS"
                    if result["test_passed"]
                    else "FAIL"
                )
            }
        )

    st.dataframe(
        validation_table,
        use_container_width=True,
        hide_index=True
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_validation, ax_validation = plt.subplots(
            figsize=(6, 4)
        )

        ax_validation.bar(
            ["Passed", "Failed"],
            [
                st.session_state["validation_passed_count"],
                st.session_state["validation_failed_count"]
            ]
        )

        ax_validation.set_title(
            "Validation Test Results"
        )
        ax_validation.set_ylabel(
            "Number of Test Cases"
        )

        st.pyplot(
            fig_validation
        )
        plt.close(fig_validation)

    with chart_col2:
        fig_coverage, ax_coverage = plt.subplots(
            figsize=(6, 4)
        )

        ax_coverage.bar(
            ["States", "Transitions"],
            [
                st.session_state["state_coverage"],
                st.session_state["transition_coverage"]
            ]
        )

        ax_coverage.set_title(
            "FSM Coverage"
        )
        ax_coverage.set_ylabel(
            "Coverage (%)"
        )
        ax_coverage.set_ylim(0, 100)

        st.pyplot(
            fig_coverage
        )
        plt.close(fig_coverage)


    # =====================================================
    # STATE DIAGRAM
    # =====================================================

    st.header(
        "8. Workflow State Diagram"
    )


    graph = nx.DiGraph()


    # Add states

    for state in fsm.states:

        graph.add_node(
            state
        )


    # Add actual FSM transitions

    for from_state, event, to_state in transitions:

        graph.add_edge(
            from_state,
            to_state,
            label=event
        )


    # -----------------------------------------------------
    # FIXED POSITIONS
    # -----------------------------------------------------

    positions = {

        "START": (0, 0),

        "LOGIN": (2, 0),

        "DASHBOARD": (4, 0),

        "CART": (6, 0),

        "PAYMENT": (8, 0),

        "ORDER_CONFIRMED": (10, 1),

        "RETRY_PAYMENT": (8, -2),

        "PROCESSING": (10, -2),

        "REFUND_APPROVED": (10, 3)

    }


    # Any unexpected states get an automatic position.

    extra_index = 0


    for state in graph.nodes:

        if state not in positions:

            positions[state] = (
                2 + extra_index,
                -4
            )

            extra_index += 1


    pos = {
        state: positions[state]
        for state in graph.nodes
    }


    # -----------------------------------------------------
    # DETERMINE NODE CATEGORIES
    # -----------------------------------------------------

    normal_nodes = []

    final_nodes = []

    unreachable_nodes = []

    dead_end_nodes = []


    for state in graph.nodes:

        if state in unreachable:

            unreachable_nodes.append(
                state
            )

        elif (
            state in dead_ends
            and state not in fsm.final_states
        ):

            dead_end_nodes.append(
                state
            )

        elif state in fsm.final_states:

            final_nodes.append(
                state
            )

        else:

            normal_nodes.append(
                state
            )


    # -----------------------------------------------------
    # DRAW GRAPH
    # -----------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(16, 8)
    )


    # Normal states

    if normal_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=normal_nodes,
            node_size=3000,
            ax=ax
        )


    # Final states

    if final_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=final_nodes,
            node_size=3500,
            node_shape="s",
            ax=ax
        )


    # Unreachable states

    if unreachable_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=unreachable_nodes,
            node_size=3500,
            node_shape="X",
            ax=ax
        )


    # Dead-end states

    if dead_end_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=dead_end_nodes,
            node_size=3500,
            node_shape="D",
            ax=ax
        )


    # Edges

    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=True,
        arrowsize=20,
        width=1.8,
        ax=ax
    )


    # Labels

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=9,
        font_weight="bold",
        ax=ax
    )


    # Edge labels

    edge_labels = (
        nx.get_edge_attributes(
            graph,
            "label"
        )
    )


    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=8,
        ax=ax
    )


    ax.set_title(
        "ReqVerify AI — Generated Finite State Machine",
        fontsize=15,
        fontweight="bold"
    )


    ax.axis("off")


    st.pyplot(
        fig
    )

    plt.close(fig)


    # =====================================================
    # DIAGRAM LEGEND
    # =====================================================

    st.markdown(
        """
        **Diagram Legend**

        - **Circle** → Normal workflow state
        - **Square** → Final/accepting state
        - **X** → Unreachable state
        - **Diamond** → Dead-end state
        """
    )


    # =====================================================
    # FINAL VERIFICATION SUMMARY
    # =====================================================

    st.header(
        "Final Verification Summary"
    )

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric(
            "Requirements Analyzed",
            len(extracted_requirements)
        )

    with summary_col2:
        st.metric(
            "FSM States",
            len(fsm.states)
        )

    with summary_col3:
        st.metric(
            "FSM Transitions",
            len(transitions)
        )

    with summary_col4:
        st.metric(
            "Structural Issues",
            len(unreachable) + len(dead_ends)
        )

    summary_col5, summary_col6, summary_col7, summary_col8 = st.columns(4)

    with summary_col5:
        st.metric(
            "Consistency Issues",
            len(consistency_issues)
        )

    with summary_col6:
        st.metric(
            "Validation Passed",
            st.session_state["validation_passed_count"]
        )

    with summary_col7:
        st.metric(
            "Validation Failed",
            st.session_state["validation_failed_count"]
        )

    with summary_col8:
        st.metric(
            "Test Suite Agreement",
            f"{st.session_state['validation_rate']:.1f}%"
        )

    st.markdown(
        f"""
        **FSM Coverage**

        - State Coverage: **{st.session_state['state_coverage']:.1f}%**
        - Transition Coverage: **{st.session_state['transition_coverage']:.1f}%**
        """
    )

    if total_issues == 0:
        st.success(
            "✓ FINAL RESULT: The supplied requirements produced an FSM "
            "with no detected structural or supported consistency issues."
        )
    else:
        st.warning(
            f"⚠ FINAL RESULT: {total_issues} verification issue(s) "
            "were detected and explained above."
        )

    # =====================================================
    # VERIFICATION REPORT
    # =====================================================

    st.header(
        "9. Verification Report"
    )


    st.download_button(
        label="⬇ Download Verification Report",
        data=verification_report,
        file_name="ReqVerify_Verification_Report.txt",
        mime="text/plain",
        key="download_report"
    )


    st.success(
        "Analysis completed successfully."
    )