from anki.collection import Collection, OpChanges
from aqt import gui_hooks, mw
from aqt.operations import CollectionOp
from aqt.utils import showInfo, showWarning


def setup_addon() -> None:
    """Standard AADT entry point."""
    # Menu integration
    action = mw.form.menuTools.addAction("My Addon")
    if action is not None:
        action.triggered.connect(main_function)

    # Hook integration
    gui_hooks.state_did_change.append(on_state_change)
    gui_hooks.operation_did_execute.append(on_operation_done)


def main_function() -> None:
    """Main addon functionality."""
    if not mw.col:
        showWarning("Please open a profile first")
        return

    # Use modern operation pattern
    def process_collection(col: Collection) -> OpChanges:
        # Your logic here
        # return col.some_operation()
        showInfo("Addon function called!")
        return OpChanges()

    CollectionOp(parent=mw, op=process_collection).success(
        lambda changes: showInfo("Operation completed!")
    ).run_in_background()


def on_state_change(new_state: str, old_state: str) -> None:
    """Handle state changes."""
    pass


def on_operation_done(changes: OpChanges, initiator: object) -> None:
    """Handle operation completion."""
    pass


# Auto-execution
setup_addon()
