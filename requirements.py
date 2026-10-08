import re
from typing import Dict, List


NON_FUNCTIONAL_HINTS = {
    "performance",
    "response time",
    "latency",
    "throughput",
    "availability",
    "reliability",
    "scalability",
    "usability",
    "maintainability",
    "portability",
    "security requirement",
    "capacity",
    "load",
    "recovery time",
}


REQUIREMENT_VERBS = re.compile(
    r"\b("
    r"shall|must|should|will|can|may|"
    r"allows?|enables?|supports?|provides?|"
    r"requires?|lets?|permits?|prevents?|ensures?"
    r")\b",
    re.IGNORECASE,
)


ID_RE = re.compile(
    r"^\s*"
    r"(?P<id>(?:FR|REQ|FREQ|NFR|R)[-_ ]?\d+)"
    r"\s*[:.)-]?\s*"
    r"(?P<title>.*)$",
    re.IGNORECASE,
)


NUM_RE = re.compile(
    r"^\s*"
    r"(?P<num>\d+(?:\.\d+)*)"
    r"[\s.)-]+"
    r"(?P<title>.+?)"
    r"\s*$"
)


BULLET_RE = re.compile(
    r"^\s*(?:[-*•▪◦]|\(\w+\))\s+(?P<text>.+)$"
)


def _clean(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    return text.strip()


def _looks_like_heading(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if len(line) > 100:
        return False

    if line.endswith((".", "?", ";", ":")):
        return False

    if ID_RE.match(line):
        return True

    if NUM_RE.match(line):
        return True

    # Short lines without requirement verbs are often headings.
    if len(line.split()) <= 10:
        if not REQUIREMENT_VERBS.search(line):
            return True

    return False


def _is_non_functional(
    description: str,
    title: str = ""
) -> bool:

    text = f"{title} {description}".lower()

    if re.search(r"\bNFR[-_ ]?\d+\b", text):
        return True

    for hint in NON_FUNCTIONAL_HINTS:
        if hint in text:
            return True

    return False


def _extract_action(text: str) -> str:

    patterns = [

        r"\b(?:the\s+)?"
        r"(?:user|system|application|service|"
        r"administrator|admin|customer)\s+"
        r"(?:can|shall|must|may|will|should|"
        r"is able to|allows? to|enables?)\s+"
        r"([^.;]+)",

        r"\b(?:user|system|application|service|"
        r"administrator|admin|customer)\s+"
        r"([^.;]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return ""


def _extract_condition(text: str) -> str:

    match = re.search(
        r"\b(?:if|when|whenever|once|after|"
        r"before|until|unless)\b([^.;]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).strip()

    return ""


def _extract_outcome(text: str) -> str:

    patterns = [

        r"\b([^.;]+?)\s+"
        r"(?:becomes?|is|are|gets?)\s+"
        r"([^.;]+)",

        r"\b(?:the\s+)?system\s+"
        r"(?:then\s+)?([^.;]+)",

        r"\b(?:allows?|enables?|permits?)\s+"
        r"(?:the\s+)?(?:user\s+)?to\s+"
        r"([^.;]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            if len(match.groups()) == 2:

                return (
                    f"{match.group(1).strip()} "
                    f"{match.group(2).strip()}"
                )

            return match.group(1).strip()

    return ""


def _make_requirement(
    req_id: str,
    title: str,
    description: str,
    source_index: int,
) -> Dict:

    description = _clean(description)

    title = _clean(title).strip(":- ")

    if not title:

        title = description[:70]

    requirement_type = (
        "Non-Functional"
        if _is_non_functional(
            description,
            title
        )
        else "Functional"
    )

    return {

        "id": req_id,

        "type": requirement_type,

        "title": title,

        "description": description,

        "actor": "",

        "action": _extract_action(
            description
        ),

        "condition": _extract_condition(
            description
        ),

        "outcome": _extract_outcome(
            description
        ),

        "source_index": source_index,
    }


def extract_requirements(
    text: str
) -> List[Dict]:

    """
    Extract functional and non-functional requirements
    from common SRS structures.

    Supported structures include:

    - FR1: ...
    - REQ-01: ...
    - 1. Login
      description...
    - bullet requirements
    - plain requirement sentences
    - grouped requirement sections
    """

    text = _clean(text or "")

    if not text:
        return []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    records = []

    current = None

    auto_id = 1

    def flush_current():

        nonlocal current
        nonlocal auto_id

        if current is None:
            return

        description = " ".join(
            current["body"]
        ).strip()

        title = current["title"]

        if description:

            req_id = (
                current["id"]
                if current["id"]
                else f"FR{auto_id}"
            )

            if not current["id"]:
                auto_id += 1

            records.append(
                _make_requirement(
                    req_id,
                    title,
                    description,
                    len(records) + 1,
                )
            )

        elif title and REQUIREMENT_VERBS.search(title):

            req_id = (
                current["id"]
                if current["id"]
                else f"FR{auto_id}"
            )

            if not current["id"]:
                auto_id += 1

            records.append(
                _make_requirement(
                    req_id,
                    title,
                    title,
                    len(records) + 1,
                )
            )

        current = None

    for line in lines:

        id_match = ID_RE.match(line)

        number_match = NUM_RE.match(line)

        bullet_match = BULLET_RE.match(line)

        # --------------------------------------------------
        # Explicit requirement ID
        # --------------------------------------------------

        if id_match:

            flush_current()

            current = {

                "id": (
                    id_match
                    .group("id")
                    .upper()
                    .replace(" ", "")
                ),

                "title": (
                    id_match
                    .group("title")
                    .strip()
                ),

                "body": [],
            }

            continue

        # --------------------------------------------------
        # Numbered requirement section
        # --------------------------------------------------

        if number_match:

            flush_current()

            current = {

                "id": None,

                "title": (
                    number_match
                    .group("title")
                    .strip()
                ),

                "body": [],
            }

            continue

        # --------------------------------------------------
        # Bullet
        # --------------------------------------------------

        if bullet_match:

            bullet_text = (
                bullet_match
                .group("text")
                .strip()
            )

            if (
                current is not None
                and current["title"]
                and not current["body"]
            ):

                current["body"].append(
                    bullet_text
                )

            else:

                flush_current()

                current = {

                    "id": None,

                    "title": "",

                    "body": [
                        bullet_text
                    ],
                }

            continue

        # --------------------------------------------------
        # Existing requirement section
        # --------------------------------------------------

        if current is not None:

            current["body"].append(
                line
            )

            continue

        # --------------------------------------------------
        # Standalone requirement sentence
        # --------------------------------------------------

        if REQUIREMENT_VERBS.search(line):

            current = {

                "id": None,

                "title": "",

                "body": [line],
            }

            continue

        # --------------------------------------------------
        # Possible heading
        # --------------------------------------------------

        if _looks_like_heading(line):

            current = {

                "id": None,

                "title": line,

                "body": [],
            }

    flush_current()

    # ------------------------------------------------------
    # Fallback for plain prose
    # ------------------------------------------------------

    if not records:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if REQUIREMENT_VERBS.search(
                sentence
            ):

                records.append(
                    _make_requirement(
                        f"FR{len(records) + 1}",
                        "",
                        sentence,
                        len(records) + 1,
                    )
                )

    # ------------------------------------------------------
    # Remove duplicates
    # ------------------------------------------------------

    unique = []

    seen = set()

    for requirement in records:

        key = re.sub(
            r"\s+",
            " ",
            requirement["description"].lower()
        )

        if (
            key
            and key not in seen
        ):

            seen.add(key)

            unique.append(
                requirement
            )

    return unique