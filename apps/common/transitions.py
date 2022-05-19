from typing import Callable
from functools import partial
from transitions import Machine, MachineError
from apps.common.exceptions import BadStateException


def change_state(callback: Callable, error_msg: str or None, *args, **kwargs):
    try:
        callback(*args, **kwargs)
    except MachineError:
        raise BadStateException(error_msg)


class StateMachineMixinBase:
    def __init__(self, *args, **kwargs):
        super(StateMachineMixinBase, self).__init__(*args, **kwargs)
        setattr(self, self.model_attribute + '_machine', Machine(
            model=None,
            auto_transitions=False,
            model_attribute=self.model_attribute,

            transitions=self.transitions,
            states=self.states,
            **self.extra_args
        ))

    transitions = None # Override!
    states = None # Override!
    model_attribute = None # Override!
    extra_args = {} # Необязательные аргументы для передачи в Machine класс

    def __getattribute__(self, item):
        """Propagate events to the workflow state machine."""

        try:
            return super(StateMachineMixinBase, self).__getattribute__(item)
        except AttributeError:
            if item in getattr(self, self.model_attribute + '_machine').events:
                return partial(getattr(self, self.model_attribute + '_machine').events[item].trigger, self)
            raise

    @property
    def state(self):
        return self.status

    @state.setter
    def state(self, value):
        self.status = value
