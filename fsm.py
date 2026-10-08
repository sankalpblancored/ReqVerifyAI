from collections import deque


class FiniteStateMachine:

    def __init__(self):

        self.states = set()

        self.transitions = {}

        self.start_state = None

        self.final_states = set()

    # ------------------------------------------------------
    # States
    # ------------------------------------------------------

    def add_state(self, state):

        self.states.add(state)

        self.transitions.setdefault(
            state,
            []
        )

    def set_start_state(self, state):

        self.add_state(state)

        self.start_state = state

    def add_final_state(self, state):

        self.add_state(state)

        self.final_states.add(state)

    # ------------------------------------------------------
    # Transitions
    # ------------------------------------------------------

    def add_transition(
        self,
        from_state,
        event,
        to_state
    ):

        self.add_state(
            from_state
        )

        self.add_state(
            to_state
        )

        transition = (
            event,
            to_state
        )

        if transition not in self.transitions[
            from_state
        ]:

            self.transitions[
                from_state
            ].append(
                transition
            )

    # ------------------------------------------------------
    # Reachability
    # ------------------------------------------------------

    def get_reachable_states(self):

        if self.start_state is None:

            return set()

        visited = {
            self.start_state
        }

        queue = deque([
            self.start_state
        ])

        while queue:

            state = queue.popleft()

            for _, next_state in self.transitions.get(
                state,
                []
            ):

                if next_state not in visited:

                    visited.add(
                        next_state
                    )

                    queue.append(
                        next_state
                    )

        return visited

    # ------------------------------------------------------
    # Unreachable
    # ------------------------------------------------------

    def get_unreachable_states(self):

        return (
            self.states
            - self.get_reachable_states()
        )

    # ------------------------------------------------------
    # Dead ends
    # ------------------------------------------------------

    def get_dead_end_states(self):

        reachable = (
            self.get_reachable_states()
        )

        return {

            state

            for state in reachable

            if (
                state
                not in self.final_states
                and len(
                    self.transitions.get(
                        state,
                        []
                    )
                ) == 0
            )
        }

    # ------------------------------------------------------
    # Sequence validation
    # ------------------------------------------------------

    def check_sequence(
        self,
        events
    ):

        if self.start_state is None:

            return False

        current_state = (
            self.start_state
        )

        for event in events:

            matches = [

                next_state

                for transition_event, next_state

                in self.transitions.get(
                    current_state,
                    []
                )

                if transition_event == event
            ]

            if not matches:

                return False

            current_state = matches[0]

        return (
            current_state
            in self.final_states
        )

    # ------------------------------------------------------
    # Transition count
    # ------------------------------------------------------

    def get_transition_count(self):

        return sum(
            len(transitions)
            for transitions
            in self.transitions.values()
        )