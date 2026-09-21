from fsm import FiniteStateMachine


fsm = FiniteStateMachine()

# Initial state
fsm.set_start_state("START")

# Normal workflow
fsm.add_transition("START", "login", "LOGIN")
fsm.add_transition("LOGIN", "success", "DASHBOARD")
fsm.add_transition("DASHBOARD", "add_item", "CART")
fsm.add_transition("CART", "checkout", "PAYMENT")
fsm.add_transition("PAYMENT", "success", "ORDER_CONFIRMED")

# Final state
fsm.add_final_state("ORDER_CONFIRMED")

# -----------------------------
# Faulty states for testing
# -----------------------------

# Reachable dead-end state
fsm.add_transition("PAYMENT", "processing", "PROCESSING")

# Unreachable state
fsm.add_state("REFUND_APPROVED")


print("All states:")
print(fsm.states)

print("\nReachable states:")
print(fsm.get_reachable_states())

print("\nUnreachable states:")
print(fsm.get_unreachable_states())

print("\nDead-end states:")
print(fsm.get_dead_end_states())

print("\nSequence Tests:")

valid_sequence = ["login", "success", "add_item", "checkout", "success"]

result, message = fsm.check_sequence(valid_sequence)

print("Valid sequence:")
print(result)
print(message)


invalid_sequence = ["login", "checkout"]

result, message = fsm.check_sequence(invalid_sequence)

print("\nInvalid sequence:")
print(result)
print(message)