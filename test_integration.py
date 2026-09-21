from parser import parse_requirements
from fsm import FiniteStateMachine


requirements = """
User logs in.
After successful login, dashboard is displayed.
User adds product to cart.
User proceeds to payment.
Successful payment confirms the order.
"""


# -----------------------------
# Parse requirements
# -----------------------------

transitions = parse_requirements(requirements)


# -----------------------------
# Create FSM
# -----------------------------

fsm = FiniteStateMachine()

fsm.set_start_state("START")


# Add extracted transitions
for from_state, event, to_state in transitions:
    fsm.add_transition(
        from_state,
        event,
        to_state
    )


# Final state
fsm.add_final_state("ORDER_CONFIRMED")


# -----------------------------
# Display results
# -----------------------------

print("=== EXTRACTED WORKFLOW ===")

for from_state, event, to_state in transitions:
    print(
        f"{from_state} --{event}--> {to_state}"
    )


print("\n=== VERIFICATION ===")

print("\nAll states:")
print(fsm.states)

print("\nReachable states:")
print(fsm.get_reachable_states())

print("\nUnreachable states:")
print(fsm.get_unreachable_states())

print("\nDead-end states:")
print(fsm.get_dead_end_states())