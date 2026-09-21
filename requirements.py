def extract_requirements(text):
    """
    Extract simple functional requirements from SRS text.
    """

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    requirements = []

    for line in lines:

        lower = line.lower()

        # Ignore document headings
        if (
            lower.startswith("software requirements")
            or lower.startswith("functional requirements")
            or lower[0:2].isdigit()
        ):
            # Keep numbered requirement sentences if they contain
            # meaningful workflow keywords.
            if not any(
                keyword in lower
                for keyword in [
                    "user",
                    "login",
                    "dashboard",
                    "payment",
                    "cart",
                    "order",
                    "retry"
                ]
            ):
                continue

        # Classify workflow-related sentences
        if any(
            keyword in lower
            for keyword in [
                "login",
                "logs in",
                "dashboard",
                "cart",
                "payment",
                "order",
                "retry"
            ]
        ):
            requirements.append({
                "type": "Functional Requirement",
                "description": line
            })

    return requirements