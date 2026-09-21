import re


def clean_line(line):
    line = line.strip()

    line = re.sub(
        r"^\s*(FR|REQ|R)?\s*\d+[\s.:\-)]*",
        "",
        line,
        flags=re.IGNORECASE
    )

    return line.strip().rstrip(".")


def contains_any(text, keywords):
    return any(
        keyword in text
        for keyword in keywords
    )


def parse_requirements(requirements):
    """
    Convert natural-language software requirements
    into FSM transitions using lightweight
    rule-based NLP.
    """

    lines = requirements.split("\n")

    transitions = []

    current_state = "START"

    login_detected = False
    dashboard_detected = False
    cart_detected = False
    payment_detected = False
    order_detected = False

    for raw_line in lines:

        line = clean_line(raw_line)

        if not line:
            continue

        text = line.lower()

        # =================================================
        # LOGIN
        # =================================================

        login_patterns = [
            "user logs in",
            "user login",
            "user logs into",
            "user signs in",
            "user sign in",
            "customer logs in",
            "customer logs into",
            "customer signs in",
            "customer sign in",
            "user authenticates",
            "user authentication",
            "customer authenticates",
            "customer authentication",
            "login to the system",
            "login into the system",
            "signs into the system",
            "sign in to the system"
        ]

        if (
            contains_any(text, login_patterns)
            and not login_detected
        ):

            transitions.append(
                (
                    current_state,
                    "login",
                    "LOGIN"
                )
            )

            current_state = "LOGIN"
            login_detected = True

            continue


        # =================================================
        # DASHBOARD
        # =================================================

        dashboard_patterns = [
            "dashboard is displayed",
            "dashboard is shown",
            "dashboard appears",
            "dashboard is available",
            "dashboard is presented",
            "dashboard displayed",
            "dashboard shown",
            "access the dashboard",
            "opens the dashboard",
            "dashboard"
        ]

        successful_login_patterns = [
            "successful login",
            "after login",
            "after logging in",
            "after signing in",
            "after authentication",
            "once authenticated",
            "when authenticated",
            "upon login"
        ]

        if (
            contains_any(text, dashboard_patterns)
            and (
                contains_any(
                    text,
                    successful_login_patterns
                )
                or login_detected
            )
            and not dashboard_detected
        ):

            transitions.append(
                (
                    "LOGIN",
                    "success",
                    "DASHBOARD"
                )
            )

            current_state = "DASHBOARD"
            dashboard_detected = True

            continue


        # =================================================
        # CART
        # =================================================

        cart_patterns = [
            "add products to cart",
            "add product to cart",
            "add items to cart",
            "add item to cart",
            "add products into cart",
            "add product into cart",
            "add items into cart",
            "add item into cart",
            "shopping cart",
            "cart",
            "add to cart",
            "adds products",
            "adds product",
            "adds items",
            "adds item"
        ]

        if (
            contains_any(text, cart_patterns)
            and not cart_detected
        ):

            transitions.append(
                (
                    current_state,
                    "add_item",
                    "CART"
                )
            )

            current_state = "CART"
            cart_detected = True

            continue


        # =================================================
        # PAYMENT / CHECKOUT
        # =================================================

        payment_patterns = [
            "payment",
            "make a payment",
            "make payment",
            "proceed to payment",
            "proceeds to payment",
            "payment page",
            "payment screen",
            "transaction",
            "checkout",
            "proceed to checkout",
            "proceeds to checkout",
            "go to checkout"
        ]

        payment_success_patterns = [
            "payment succeeds",
            "payment is successful",
            "successful payment",
            "payment successful",
            "transaction succeeds",
            "transaction is successful",
            "transaction successful",
            "payment completed",
            "payment is completed",
            "transaction completed"
        ]

        payment_failure_patterns = [
            "payment fails",
            "payment failed",
            "payment is unsuccessful",
            "payment unsuccessful",
            "transaction fails",
            "transaction failed",
            "transaction is unsuccessful",
            "transaction unsuccessful",
            "payment error",
            "payment failure"
        ]

        cancel_patterns = [
            "cancel payment",
            "cancels payment",
            "cancel the payment",
            "cancels the payment",
            "payment is cancelled",
            "payment is canceled",
            "payment cancelled",
            "payment canceled",
            "user cancels payment",
            "customer cancels payment",
            "user cancels the payment",
            "customer cancels the payment"
        ]

        retry_patterns = [
            "retry payment",
            "retry the payment",
            "retry",
            "try again",
            "attempt payment again",
            "make another payment",
            "payment can be retried"
        ]

        order_confirmation_patterns = [
            "order is confirmed",
            "order confirmed",
            "order is placed",
            "order placed",
            "order is created",
            "order created",
            "purchase is confirmed",
            "purchase confirmed",
            "order confirmation"
        ]

        is_success_condition = contains_any(
            text,
            payment_success_patterns
        )

        is_failure_condition = contains_any(
            text,
            payment_failure_patterns
        )

        is_cancel_condition = contains_any(
            text,
            cancel_patterns
        )


        # =================================================
        # CANCEL BRANCH
        # =================================================

        if is_cancel_condition:

            transitions.append(
                (
                    "PAYMENT",
                    "cancel",
                    "ORDER_CANCELLED"
                )
            )

            current_state = "ORDER_CANCELLED"

            continue


        # =================================================
        # PAYMENT STATE
        # =================================================

        if (
            contains_any(
                text,
                payment_patterns
            )
            and not is_success_condition
            and not is_failure_condition
            and not is_cancel_condition
            and not payment_detected
        ):

            transitions.append(
                (
                    current_state,
                    "checkout",
                    "PAYMENT"
                )
            )

            current_state = "PAYMENT"
            payment_detected = True

            continue


        # =================================================
        # SUCCESSFUL PAYMENT
        # =================================================

        if (
            is_success_condition
            and contains_any(
                text,
                order_confirmation_patterns
            )
        ):

            transitions.append(
                (
                    "PAYMENT",
                    "success",
                    "ORDER_CONFIRMED"
                )
            )

            current_state = "ORDER_CONFIRMED"
            order_detected = True

            continue


        # =================================================
        # PAYMENT FAILURE + RETRY
        # =================================================

        if (
            is_failure_condition
            and contains_any(
                text,
                retry_patterns
            )
        ):

            transitions.append(
                (
                    "PAYMENT",
                    "failure",
                    "RETRY_PAYMENT"
                )
            )

            transitions.append(
                (
                    "RETRY_PAYMENT",
                    "retry",
                    "PAYMENT"
                )
            )

            current_state = "PAYMENT"

            continue


        # =================================================
        # PAYMENT SUCCESS WITHOUT EXPLICIT ORDER PHRASE
        # =================================================

        if (
            is_success_condition
            and not order_detected
        ):

            transitions.append(
                (
                    "PAYMENT",
                    "success",
                    "ORDER_CONFIRMED"
                )
            )

            current_state = "ORDER_CONFIRMED"
            order_detected = True

            continue


        # =================================================
        # PAYMENT FAILURE WITHOUT RETRY
        # =================================================

        if (
            is_failure_condition
            and not contains_any(
                text,
                retry_patterns
            )
        ):

            transitions.append(
                (
                    "PAYMENT",
                    "failure",
                    "PAYMENT_FAILED"
                )
            )

            current_state = "PAYMENT_FAILED"

            continue


    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_transitions = []

    for transition in transitions:

        if transition not in unique_transitions:

            unique_transitions.append(
                transition
            )

    return unique_transitions