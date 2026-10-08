import re
from typing import Dict, List, Tuple, Optional


Transition = Tuple[str, str, str]


# =========================================================
# BASIC TEXT HELPERS
# =========================================================

def _clean(text):
    return re.sub(
        r"\s+",
        " ",
        str(text or "")
    ).strip()


def _norm(text):

    text = str(text or "").upper()

    # Remove condition words from the beginning.
    text = re.sub(
        r"^\s*(WHEN|IF|AFTER|BEFORE|ONCE|UPON|"
        r"WHILE|UNTIL|UNLESS)\s+",
        "",
        text,
    )

    # Remove common grammatical prefixes.
    text = re.sub(
        r"^\s*(THE|A|AN)\s+",
        "",
        text,
    )

    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if not text:
        return "STATE"

    return text.replace(
        " ",
        "_"
    )


# =========================================================
# STATE GENERATION
# =========================================================

def _title_state(title):

    title = _clean(
        title
    )

    title = re.sub(
        r"\b(requirement|process|feature)\b",
        " ",
        title,
        flags=re.IGNORECASE,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    title = re.sub(
        r"^(user|system|application)\s+",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return _norm(title)


def _target_state(requirement):

    title = requirement.get(
        "title",
        ""
    )

    description = _clean(
        requirement.get(
            "description",
            ""
        )
    )

    text = description.lower()

    # ------------------------------------------------------
    # Explicit outcome states
    # ------------------------------------------------------

    patterns = [

        # "account becomes active"
        (
            r"\b([a-z][a-z0-9 _-]*?)\s+"
            r"becomes?\s+"
            r"([a-z][a-z0-9 _-]*)\b",

            lambda m:
                _norm(
                    m.group(1)
                )
                + "_"
                + _norm(
                    m.group(2)
                )
        ),

        # "order is confirmed"
        # "appointment is confirmed"
        # "record is updated"
        (
            r"\b(?:the\s+)?"
            r"([a-z][a-z0-9 _-]*?)\s+"
            r"(?:is|are)\s+"
            r"(?:successfully\s+)?"
            r"(confirmed|activated|completed|"
            r"approved|verified|rejected|"
            r"cancelled|canceled|created|"
            r"updated|closed|finished)\b",

            lambda m:
                _norm(
                    m.group(1)
                )
                + "_"
                + _norm(
                    m.group(2)
                )
        ),

        # "system sends a verification email"
        (
            r"\bsystem\s+sends?\s+"
            r"(?:a|an|the)\s+"
            r"([^.;]+)",

            lambda m:
                _norm(
                    m.group(1)
                )
        ),

        # "allows the user to request a password reset"
        (
            r"\b(?:allows?|enables?|permits?)\s+"
            r"(?:the\s+)?(?:user\s+)?to\s+"
            r"(?:request|create|submit|generate)\s+"
            r"(?:a|an|the)?\s*"
            r"([^.;]+)",

            lambda m:
                _norm(
                    m.group(1)
                )
                + "_REQUESTED"
        ),

        # "a new password can be created"
        (
            r"\b(?:a|an|the)\s+new\s+"
            r"([a-z][a-z0-9 _-]+?)\s+"
            r"can\s+be\s+created\b",

            lambda m:
                _norm(
                    m.group(1)
                )
                + "_CREATED"
        ),
    ]

    for pattern, builder in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            state = builder(match)

            if state not in {
                "STATE",
                "SYSTEM",
            }:

                return state

    # ------------------------------------------------------
    # Fallback: use requirement title
    # ------------------------------------------------------

    return _title_state(
        title
        or description[:60]
    )


# =========================================================
# EVENT EXTRACTION
# =========================================================

# Common workflow verbs.
# These are generic software/process actions, not domain-specific
# states such as PAYMENT, CART, PATIENT, etc.
EVENT_VERBS = [
    "log in",
    "login",
    "sign in",
    "authenticate",
    "register",
    "create",
    "book",
    "schedule",
    "submit",
    "send",
    "verify",
    "activate",
    "confirm",
    "approve",
    "reject",
    "cancel",
    "complete",
    "finish",
    "update",
    "delete",
    "remove",
    "add",
    "select",
    "choose",
    "enter",
    "click",
    "upload",
    "download",
    "request",
    "generate",
    "open",
    "close",
    "view",
    "display",
    "proceed",
    "checkout",
    "retry",
    "reset",
    "change",
    "conduct",
    "perform",
    "process",
    "validate",
    "search",
    "filter",
    "edit",
    "save",
    "scan",
    "scan",
    "pay",
    "purchase",
    "transfer",
    "browse",
    "place",
    "prepare",
    "assign",
    "deliver",
    "mark",
    "return",
    "record",
    "issue",
]


def _canonical_event(verb):

    verb = _clean(
        verb
    ).lower()

    verb = re.sub(
        r"\s+",
        " ",
        verb,
    )

    mapping = {

        "log in":
            "login",

        "login":
            "login",

        "sign in":
            "login",

        "authenticate":
            "authenticate",

        "logs in":
            "login",

        "register":
            "register",

        "registers":
            "register",

        "creates":
            "create",

        "create":
            "create",

        "books":
            "book",

        "book":
            "book",

        "schedules":
            "schedule",

        "schedule":
            "schedule",

        "submits":
            "submit",

        "submit":
            "submit",

        "sends":
            "send",

        "send":
            "send",

        "verifies":
            "verify",

        "verify":
            "verify",

        "activates":
            "activate",

        "activate":
            "activate",

        "confirms":
            "confirm",

        "confirm":
            "confirm",

        "approves":
            "approve",

        "approve":
            "approve",

        "rejects":
            "reject",

        "reject":
            "reject",

        "cancels":
            "cancel",

        "cancel":
            "cancel",

        "completes":
            "complete",

        "complete":
            "complete",

        "finishes":
            "finish",

        "finish":
            "finish",

        "updates":
            "update",

        "update":
            "update",

        "deletes":
            "delete",

        "delete":
            "delete",

        "removes":
            "remove",

        "remove":
            "remove",

        "adds":
            "add",

        "add":
            "add",

        "selects":
            "select",

        "select":
            "select",

        "chooses":
            "choose",

        "choose":
            "choose",

        "enters":
            "enter",

        "enter":
            "enter",

        "clicks":
            "click",

        "click":
            "click",

        "uploads":
            "upload",

        "upload":
            "upload",

        "downloads":
            "download",

        "download":
            "download",

        "requests":
            "request",

        "request":
            "request",

        "generates":
            "generate",

        "generate":
            "generate",

        "opens":
            "open",

        "open":
            "open",

        "closes":
            "close",

        "close":
            "close",

        "views":
            "view",

        "view":
            "view",

        "displays":
            "display",

        "display":
            "display",

        "proceeds":
            "proceed",

        "proceed":
            "proceed",

        "checkout":
            "checkout",

        "retries":
            "retry",

        "retry":
            "retry",

        "resets":
            "reset",

        "reset":
            "reset",

        "changes":
            "change",

        "change":
            "change",

        "conducts":
            "conduct",

        "conduct":
            "conduct",

        "performs":
            "perform",

        "perform":
            "perform",

        "processes":
            "process",

        "process":
            "process",

        "validates":
            "validate",

        "validate":
            "validate",

        "searches":
            "search",

        "search":
            "search",

        "filters":
            "filter",

        "filter":
            "filter",

        "edits":
            "edit",

        "edit":
            "edit",

        "saves":
            "save",

        "save":
            "save",

        "scans":
            "scan",

        "scan":
            "scan",

        "pays":
            "pay",

        "pay":
            "pay",

        "purchases":
            "purchase",

        "purchase":
            "purchase",

        "transfers":
            "transfer",

        "browses":
            "browse",

        "browse":
            "browse",

        "places":
            "place",

        "place":
            "place",

        "assigns":
            "assign",

        "assign":
            "assign",

        "prepares":
            "prepare",

        "prepare":
            "prepare",

        "delivers":
            "deliver",

        "deliver":
            "deliver",

        "marks":
            "mark",

        "mark":
            "mark",

        "returns":
            "return",

        "return":
            "return",

        "records":
            "record",

        "record":
            "record",

        "issues":
            "issue",

        "issue":
            "issue",
            
    "browses": "browse",
    "browse": "browse",
    "places": "place",
    "place": "place",
    "prepares": "prepare",
    "prepare": "prepare",
    "assigns": "assign",
    "assign": "assign",
    "delivers": "deliver",
    "deliver": "deliver",
    "marks": "mark",
    "mark": "mark",
    "returns": "return",
    "return": "return",
    "records": "record",
    "record": "record",
    "issues": "issue",
    "issue": "issue",    
    }

    return mapping.get(
        verb,
        verb.replace(
            " ",
            "_"
        ),
    )

def _event_from_text(text: str) -> Optional[str]:
    """
    Extract a workflow event/action from natural-language requirement text.

    The extractor is domain-independent. It prioritizes known action verbs
    instead of treating actors, nouns, or relationship words as events.
    """

    if not text:
        return None

    text = _clean(text)
    if not text:
        return None

    # ---------------------------------------------------------
    # 1. Explicit success / failure conditions
    # ---------------------------------------------------------
    lower = text.lower()

    # Remove prerequisite/condition clauses so that the
    # action in the main clause is selected.
    main_clause = re.sub(
        r"^\s*(?:after|when|once|upon|if)\b.*?(?:,|;|:)\s*",
        "",
        lower,
        count=1,
    )

    if re.search(r"\b(successfully|success)\b", main_clause):
        return "success"

    if re.search(r"\b(fail|failed|failure|unsuccessful)\b", main_clause):
        return "failure"

    # ---------------------------------------------------------
    # 2. Known workflow/action verbs
    #
    # Order matters: more specific action verbs are checked
    # before generic relationship words.
    # ---------------------------------------------------------
    action_patterns = [
        ("log in", r"\blog\s+in\b"),
        ("login", r"\blogin\b"),
        ("sign in", r"\bsign\s+in\b"),
        ("authenticate", r"\bauthenticat(?:e|es|ed|ing)\b"),

        ("register", r"\bregister(?:s|ed|ing)?\b"),
        ("create", r"\bcreat(?:e|es|ed|ing)\b"),

        ("select", r"\bselect(?:s|ed|ing)?\b"),
        ("choose", r"\bchoos(?:e|es|en|ing)\b"),
        ("place", r"\bplac(?:e|es|ed|ing)\b"),

        ("browse", r"\bbrows(?:e|es|ed|ing)\b"),
        ("search", r"\bsearch(?:es|ed|ing)?\b"),
        ("filter", r"\bfilter(?:s|ed|ing)?\b"),

        ("book", r"\bbook(?:s|ed|ing)?\b"),
        ("schedule", r"\bschedul(?:e|es|ed|ing)\b"),

        ("submit", r"\bsubmit(?:s|ted|ting)?\b"),
        ("send", r"\bsend(?:s|ing)?\b"),
        ("request", r"\brequest(?:s|ed|ing)?\b"),

        ("verify", r"\bverif(?:y|ies|ied|ying)\b"),
        ("validate", r"\bvalidat(?:e|es|ed|ing)\b"),

        ("activate", r"\bactivat(?:e|es|ed|ing)\b"),
        ("confirm", r"\bconfirm(?:s|ed|ing)?\b"),
        ("approve", r"\bapprov(?:e|es|ed|ing)\b"),
        ("reject", r"\breject(?:s|ed|ing)?\b"),

        ("cancel", r"\bcancel(?:s|ed|ing)?\b"),
        ("complete", r"\bcomplet(?:e|es|ed|ing)\b"),
        ("finish", r"\bfinish(?:es|ed|ing)?\b"),

        ("update", r"\bupdat(?:e|es|ed|ing)\b"),
        ("edit", r"\bedit(?:s|ed|ing)?\b"),
        ("save", r"\bsav(?:e|es|ed|ing)\b"),

        ("delete", r"\bdelet(?:e|es|ed|ing)\b"),
        ("remove", r"\bremov(?:e|es|ed|ing)\b"),

        ("add", r"\badd(?:s|ed|ing)?\b"),
        ("enter", r"\benter(?:s|ed|ing)?\b"),

        ("click", r"\bclick(?:s|ed|ing)?\b"),
        ("upload", r"\bupload(?:s|ed|ing)?\b"),
        ("download", r"\bdownload(?:s|ed|ing)?\b"),

        ("open", r"\bopen(?:s|ed|ing)?\b"),
        ("close", r"\bclos(?:e|es|ed|ing)\b"),
        ("view", r"\bview(?:s|ed|ing)?\b"),
        ("display", r"\bdisplay(?:s|ed|ing)?\b"),

        ("proceed", r"\bproceed(?:s|ed|ing)?\b"),
        ("checkout", r"\bcheckout\b"),
        ("retry", r"\bretr(?:y|ies|ied|ying)\b"),
        ("reset", r"\bres(?:e|ets|et|etting)\b"),
        ("change", r"\bchang(?:e|es|ed|ing)\b"),

        ("conduct", r"\bconduct(?:s|ed|ing)?\b"),
        ("perform", r"\bperform(?:s|ed|ing)?\b"),
        ("process", r"\bprocess(?:es|ed|ing)?\b"),

        ("prepare", r"\bprepar(?:e|es|ed|ing)\b"),
        ("assign", r"\bassign(?:s|ed|ing)?\b"),
        ("deliver", r"\bdeliver(?:s|ed|ing)?\b"),
        ("return", r"\breturn(?:s|ed|ing)?\b"),
        ("record", r"\brecord(?:s|ed|ing)?\b"),
        ("issue", r"\bissu(?:e|es|ed|ing)\b"),
        ("mark", r"\bmark(?:s|ed|ing)?\b"),

        ("pay", r"\bpay(?:s|ed|ing)?\b"),
        ("purchase", r"\bpurchas(?:e|es|ed|ing)\b"),
        ("transfer", r"\btransfer(?:s|red|ring)?\b"),
    ]

    # ---------------------------------------------------------
    # 3. Find all known action verbs.
    # Pick the first meaningful workflow action.
    # ---------------------------------------------------------
    matches = []

    for event, pattern in action_patterns:
        match = re.search(pattern, main_clause, re.IGNORECASE)
        if match:
            matches.append((match.start(), event))

    if matches:
        matches.sort(key=lambda item: item[0])
        return matches[0][1]
    
    # ---------------------------------------------------------
    # 4. Generic modal-action pattern.
    #
    # Example:
    # "The employee can approve the request"
    #              ^ action = approve
    # ---------------------------------------------------------
    modal_pattern = re.search(
        r"\b(?:can|may|must|shall|should|will|"
        r"is\s+able\s+to|are\s+able\s+to)\s+"
        r"([a-z]+(?:-[a-z]+)?)\b",
        main_clause,
        re.IGNORECASE,
    )

    if modal_pattern:
        return _canonical_event(modal_pattern.group(1))

    # ---------------------------------------------------------
    # 5. Generic fallback.
    #
    # Only use the first meaningful word if no known action
    # could be identified.
    # ---------------------------------------------------------
    words = re.findall(r"\b[a-zA-Z][a-zA-Z-]*\b", main_clause)

    ignored = {
        "the", "a", "an", "user", "customer", "client",
        "system", "application", "service", "patient",
        "doctor", "administrator", "admin", "manager",
        "staff", "restaurant", "delivery", "partner",
        "after", "before", "when", "once", "upon", "if",
        "then", "and", "or", "for", "to", "from", "of",
        "with", "on", "in", "into", "by", "is", "are",
        "was", "were", "be", "been", "being",
        "can", "may", "must", "shall", "should", "will",
    }

    for word in words:
        if word not in ignored and len(word) > 2:
            return _canonical_event(word)

    return None

def _event_from_requirement(
    requirement
):

    description = _clean(
        requirement.get(
            "description",
            ""
        )
    )

    action = _clean(
        requirement.get(
            "action",
            ""
        )
    )

    # Description is more reliable than the
    # automatically extracted action field for
    # determining the actual workflow verb.
    event = _event_from_text(
        description
    )

    # If description produced only a generic
    # event, try the structured action.
    if event == "event" and action:

        event = _event_from_text(
            action
        )

    return event


# =========================================================
# SOURCE STATE DETECTION
# =========================================================

def _find_referenced_source(
    requirement,
    known_states,
):

    text = _clean(
        requirement.get(
            "description",
            ""
        )
    ).lower()

    references = []

    patterns = [

        r"\bafter\s+([^.;]+)",

        r"\bwhen\s+([^.;]+)",

        r"\bonce\s+([^.;]+)",

        r"\bupon\s+([^.;]+)",

        r"\bif\s+([^.;]+)",
    ]

    for pattern in patterns:

        references.extend(
            re.findall(
                pattern,
                text
            )
        )

    for phrase in references:

        phrase_norm = _norm(
            phrase
        ).lower()

        phrase_tokens = set(
            phrase_norm.split("_")
        )

        for state in known_states:

            state_tokens = set(
                state.lower().split("_")
            )

            if (
                state_tokens
                and state_tokens <= phrase_tokens
            ):

                return state

            # Generic outcome matching.
            if (
                "activated" in phrase
                and state.endswith(
                    "_ACTIVE"
                )
            ):

                return state

            if (
                "confirmed" in phrase
                and state.endswith(
                    "_CONFIRMED"
                )
            ):

                return state

            if (
                "completed" in phrase
                and state.endswith(
                    "_COMPLETED"
                )
            ):

                return state

            if (
                "created" in phrase
                and state.endswith(
                    "_CREATED"
                )
            ):

                return state

            if (
                "verified" in phrase
                and state.endswith(
                    "_VERIFIED"
                )
            ):

                return state

    return None


# =========================================================
# REQUIREMENT → TRANSITION
# =========================================================

def parse_requirement(
    requirement,
    previous_state="START",
    known_states=None,
):

    known_states = set(
        known_states or []
    )

    target = _target_state(
        requirement
    )

    event = _event_from_requirement(
        requirement
    )

    source = _find_referenced_source(
        requirement,
        known_states,
    )

    if source is None:

        source = (
            previous_state
            or "START"
        )

    # Avoid self-loop caused by a title
    # representing the same state.
    if (
        source == target
        and source != "START"
    ):

        source = (
            previous_state
            if previous_state != target
            else "START"
        )

    return (
        source,
        event,
        target,
    )


# =========================================================
# PARSE ALL REQUIREMENTS
# =========================================================

def parse_requirements(
    requirements
) -> List[Transition]:

    """
    Accept either:

    1. Structured requirements from requirements.py
    2. Raw SRS text
    """

    if isinstance(
        requirements,
        str
    ):

        from requirements import (
            extract_requirements
        )

        requirements = (
            extract_requirements(
                requirements
            )
        )

    if not requirements:

        return []

    transitions = []

    previous_state = "START"

    known_states = {
        "START"
    }

    for requirement in requirements:

        if (
            requirement.get("type")
            == "Non-Functional"
        ):

            continue

        transition = parse_requirement(
            requirement,
            previous_state,
            known_states,
        )

        if transition not in transitions:

            transitions.append(
                transition
            )

        previous_state = (
            transition[2]
        )

        known_states.add(
            transition[2]
        )

    return transitions


# =========================================================
# FINAL STATE INFERENCE
# =========================================================

def infer_final_states(
    requirements,
    transitions
):

    if isinstance(
        requirements,
        str
    ):

        from requirements import (
            extract_requirements
        )

        requirements = (
            extract_requirements(
                requirements
            )
        )

    final_states = set()

    outgoing_states = {
        source
        for source, _, _
        in transitions
    }

    for requirement in requirements:

        if (
            requirement.get("type")
            == "Non-Functional"
        ):

            continue

        text = requirement.get(
            "description",
            ""
        ).lower()

        target = _target_state(
            requirement
        )

        if re.search(
            r"\b("
            r"confirmed|completed|"
            r"cancelled|canceled|"
            r"approved|rejected|"
            r"closed|finished|"
            r"terminated"
            r")\b",
            text,
        ):

            final_states.add(
                target
            )

    # Fallback to sink states.
    if not final_states:

        sinks = {
            target
            for _, _, target
            in transitions
            if target not in outgoing_states
        }

        if sinks:

            final_states.add(
                sorted(sinks)[-1]
            )

    return final_states