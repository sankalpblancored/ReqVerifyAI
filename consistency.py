def check_consistency(requirements):
    """
    Detect simple logical contradictions between
    software requirements.

    Returns a list of explainable consistency issues.
    """

    lines = [
        line.strip()
        for line in requirements.split("\n")
        if line.strip()
    ]

    normalized = [
        line.lower()
        for line in lines
    ]

    issues = []


    # =====================================================
    # LOGIN / DASHBOARD CONTRADICTION
    # =====================================================

    login_required_index = None
    dashboard_bypass_index = None


    for index, line in enumerate(normalized):

        if (
            "successful login" in line
            and "dashboard" in line
        ) or (
            "after login" in line
            and "dashboard" in line
        ) or (
            "after authentication" in line
            and "dashboard" in line
        ):

            login_required_index = index


        if (
            "dashboard" in line
            and (
                "without logging in" in line
                or "without login" in line
                or "without authentication" in line
                or "without signing in" in line
                or "without sign in" in line
            )
        ):

            dashboard_bypass_index = index


    if (
        login_required_index is not None
        and dashboard_bypass_index is not None
    ):

        issues.append(
            "Contradiction detected between "
            f"Requirement {login_required_index + 1} "
            f"and Requirement {dashboard_bypass_index + 1}: "
            "one requirement indicates that dashboard access "
            "follows successful authentication, while another "
            "allows dashboard access without authentication."
        )


    # =====================================================
    # PAYMENT SUCCESS / PAYMENT FAILURE CONTRADICTION
    # =====================================================

    payment_success_index = None
    payment_failure_index = None


    for index, line in enumerate(normalized):

        if (
            "payment succeeds" in line
            or "payment is successful" in line
            or "successful payment" in line
            or "payment successful" in line
        ):

            payment_success_index = index


        if (
            "payment always fails" in line
            or "payment always unsuccessful" in line
            or "payment can never succeed" in line
            or "payment never succeeds" in line
        ):

            payment_failure_index = index


    if (
        payment_success_index is not None
        and payment_failure_index is not None
    ):

        issues.append(
            "Potential payment contradiction between "
            f"Requirement {payment_success_index + 1} "
            f"and Requirement {payment_failure_index + 1}: "
            "one requirement describes successful payment "
            "while another states that payment cannot succeed."
        )


    # =====================================================
    # ORDER CONFIRMATION CONTRADICTION
    # =====================================================

    order_confirmed_index = None
    order_not_confirmed_index = None


    for index, line in enumerate(normalized):

        if (
            "order is confirmed" in line
            or "order confirmed" in line
            or "order is placed" in line
            or "order placed" in line
        ):

            order_confirmed_index = index


        if (
            "order is not confirmed" in line
            or "order not confirmed" in line
            or "order cannot be confirmed" in line
            or "order is never confirmed" in line
        ):

            order_not_confirmed_index = index


    if (
        order_confirmed_index is not None
        and order_not_confirmed_index is not None
    ):

        issues.append(
            "Potential order-confirmation contradiction between "
            f"Requirement {order_confirmed_index + 1} "
            f"and Requirement {order_not_confirmed_index + 1}: "
            "the requirements provide conflicting conditions "
            "for order confirmation."
        )


    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return issues