class DeploymentState:
    def __init__(
        self,
        completed: bool = False,
        error=None,
        has_warning: bool = False,
        state: str = None,
    ):
        self.completed = completed
        self.has_warning = has_warning
        self.error = error
        self.state = state
