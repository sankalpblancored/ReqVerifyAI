class FiniteStateMachine:

    def __init__(self):

        self.states = set()

        self.transitions = {}

        self.start_state = None

        self.final_states = set()


    # =====================================================
    # STATE MANAGEMENT
    # =====================================================

    def add_state(self, state):

        self.states.add(state)


    def set_start_state(self, state):

        self.add_state(state)

        self.start_state = state


    def add_final_state(self, state):

        self.add_state(state)

        self.final_states.add(state)


    # =====================================================
    # TRANSITIONS
    # =====================================================

    def add_transition(
        self,
        from_state,
        event,
        to_state
    ):

        self.add_state(from_state)

        self.add_state(to_state)

        if from_state not in self.transitions:

            self.transitions[from_state] = []

        self.transitions[from_state].append(
            (
                event,
                to_state
            )
        )


    # =====================================================
    # REACHABILITY
    # =====================================================

    def get_reachable_states(self):

        if self.start_state is None:

            return set()


        visited = set()

        stack = [
            self.start_state
        ]


        while stack:

            current = stack.pop()


            if current in visited:

                continue


            visited.add(current)


            for event, next_state in self.transitions.get(
                current,
                []
            ):

                if next_state not in visited:

                    stack.append(
                        next_state
                    )


        return visited


    # =====================================================
    # UNREACHABLE STATES
    # =====================================================

    def get_unreachable_states(self):

        reachable = (
            self.get_reachable_states()
        )

        return self.states - reachable


    # =====================================================
    # DEAD-END STATES
    # =====================================================

    def get_dead_end_states(self):

        dead_ends = set()


        for state in self.states:

            if state not in self.final_states:

                if (
                    state not in self.transitions
                    or len(
                        self.transitions[state]
                    ) == 0
                ):

                    dead_ends.add(
                        state
                    )


        return dead_ends


    # =====================================================
    # FSM ACCEPTANCE
    # =====================================================

    def check_sequence(self, events):

        if self.start_state is None:

            return (
                False,
                "No start state defined."
            )


        current_state = (
            self.start_state
        )


        # -------------------------------------------------
        # Process every input event
        # -------------------------------------------------

        for event in events:

            found = False


            for (
                transition_event,
                next_state
            ) in self.transitions.get(
                current_state,
                []
            ):

                if transition_event == event:

                    current_state = (
                        next_state
                    )

                    found = True

                    break


            # -------------------------------------------------
            # Invalid transition
            # -------------------------------------------------

            if not found:

                return (
                    False,
                    f"Invalid event '{event}' "
                    f"from state '{current_state}'."
                )


        # -------------------------------------------------
        # Formal acceptance condition
        # -------------------------------------------------

        if current_state in self.final_states:

            return (
                True,
                f"Accepted. Input sequence reaches "
                f"final state '{current_state}'."
            )


        # -------------------------------------------------
        # Valid transitions but non-final state
        # -------------------------------------------------

        return (
            False,
            f"Rejected. All transitions were valid, "
            f"but the sequence ends at non-final state "
            f"'{current_state}'."
        )