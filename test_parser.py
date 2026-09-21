from parser import parse_requirements


requirements = """
User logs in.
After successful login, dashboard is displayed.
User adds product to cart.
User proceeds to payment.
Successful payment confirms the order.
"""


transitions = parse_requirements(requirements)


print("Extracted Transitions:")
print()

for transition in transitions:
    from_state, event, to_state = transition

    print(
        f"{from_state} --{event}--> {to_state}"
    )