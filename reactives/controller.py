import inspect
import weakref
from collections import deque
from contextlib import contextmanager, suppress

from reactives.typing import Reactor, ReactorDefinition

try:
    from graphlib import TopologicalSorter
except ImportError:
    from graphlib_backport import TopologicalSorter
from typing import Callable, Sequence, Tuple, Optional, Dict, Set


class ReactorController:
    _trigger_suspended: bool = False
    _chain_is_reacting: bool = False
    _chain_reactor_graph: Dict[Callable, Set[Callable]] = {}
    _chain_reactors: deque = deque()
    _chain_current_reactor: Optional[Reactor] = None

    def __init__(self):
        self._reactors = []

    def __call__(self, *args, **kwargs):
        self.react(*args, **kwargs)

    def trigger(self) -> None:
        if ReactorController._trigger_suspended:
            return

        if self.trigger == ReactorController._chain_current_reactor:
            return

        self._update_reactor_graph()
        self._trigger_reactor_chain()

    def _update_reactor_graph(self) -> None:
        if len(self._reactors) == 0:
            return

        for reactor in self._reactors:
            for source_reactor, target_reactor in self._expand_reactor(None, reactor):
                if target_reactor not in ReactorController._chain_reactor_graph:
                    ReactorController._chain_reactor_graph[target_reactor] = set(
                    )
                if source_reactor is not None:
                    ReactorController._chain_reactor_graph[target_reactor].add(
                        source_reactor)

        ReactorController._chain_reactors = deque(TopologicalSorter(
            ReactorController._chain_reactor_graph).static_order())

    def _expand_reactor(self, caller: Optional[Reactor], reactor: ReactorDefinition) -> Sequence[Tuple[Optional[Reactor], Reactor]]:
        from reactives import is_reactive

        # weakref.proxy is not hashable, so we use weakref.ref and dereference it ourselves.
        if isinstance(reactor, weakref.ref):
            reactor = reactor()

        if is_reactive(reactor):
            yield caller, reactor.react.trigger
            for reactor_reactor in reactor.react._reactors:
                yield from self._expand_reactor(reactor.react.trigger, reactor_reactor)
        else:
            yield caller, reactor

    def _trigger_reactor_chain(self) -> None:
        if ReactorController._chain_is_reacting:
            return
        ReactorController._chain_is_reacting = True
        try:
            while True:
                try:
                    ReactorController._chain_current_reactor = ReactorController._chain_reactors.popleft()
                except IndexError:
                    return

                # Remove indegree vertices, if they exist. This keeps the graph as small as possible, allowing for the
                # most efficient re-tsorting if it must be extended because of branched reactors.
                with suppress(KeyError):
                    del ReactorController._chain_reactor_graph[ReactorController._chain_current_reactor]

                ReactorController._chain_current_reactor()
        finally:
            ReactorController._chain_is_reacting = False
            ReactorController._chain_current_reactor = None

    def _weakref(self, target, *args, **kwargs) -> weakref.ref:
        if inspect.ismethod(target):
            return weakref.WeakMethod(target, *args, **kwargs)
        # weakref.proxy is not hashable, so we use weakref.ref and dereference it ourselves.
        return weakref.ref(target, *args, **kwargs)

    @classmethod
    @contextmanager
    def suspend(cls) -> None:
        original_suspended = ReactorController._trigger_suspended
        ReactorController._trigger_suspended = True
        yield
        ReactorController._trigger_suspended = original_suspended

    def react(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self._reactors.append(reactor)

    def shutdown(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self._reactors.remove(reactor)

    def react_weakref(self, *reactors: ReactorDefinition) -> None:
        """
        Add a reactor using a weakref.

        This is a small helper, and it doesn't do much, but it serves as a reminder for people that it's important to
        consider using weakrefs for the performance of their application: if a reactor is added without a weakref, it
        MUST be shut down explicitly or a reference to it will exist forever, consuming memory and potentially slowing
        down reactivity.
        """
        for reactor in reactors:
            self.react(self._weakref(reactor, self._reactors.remove))

    def shutdown_weakref(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self.shutdown(self._weakref(reactor, self._reactors.remove))
