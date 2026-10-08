import re


def check_consistency(requirements):

    """
    Detect simple potential contradictions
    between requirement statements.

    This is a lightweight rule-based check.
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

    issues = []

    positive = []

    negative = []

    for requirement in requirements or []:

        text = requirement.get(
            "description",
            ""
        ).strip()

        if not text:
            continue

        low = text.lower()

        # Positive permission/requirement.
        if re.search(
            r"\b("
            r"shall|must|can|may|"
            r"should|will|allows?"
            r")\b",
            low,
        ):

            positive.append(
                requirement
            )

        # Negative restriction.
        if re.search(
            r"\b("
            r"shall not|must not|"
            r"cannot|can not|"
            r"may not|should not|"
            r"never|prohibits?"
            r")\b",
            low,
        ):

            negative.append(
                requirement
            )

    for positive_req in positive:

        positive_words = set(
            re.findall(
                r"[a-z]{4,}",
                positive_req[
                    "description"
                ].lower()
            )
        )

        for negative_req in negative:

            negative_words = set(
                re.findall(
                    r"[a-z]{4,}",
                    negative_req[
                        "description"
                    ].lower()
                )
            )

            overlap = (
                positive_words
                & negative_words
            )

            if len(overlap) >= 3:

                issues.append({

                    "type":
                        "Potential contradiction",

                    "message":
                        (
                            f"{positive_req['id']} "
                            f"and "
                            f"{negative_req['id']} "
                            "may express "
                            "conflicting behavior."
                        ),

                    "requirements": [
                        positive_req["id"],
                        negative_req["id"],
                    ],

                    "evidence":
                        (
                            f"{positive_req['description']} "
                            "/ "
                            f"{negative_req['description']}"
                        ),
                })

    return issues