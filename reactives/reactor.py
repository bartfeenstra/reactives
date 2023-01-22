from __future__ import annotations

import copy
import inspect
import weakref
from _weakref import ReferenceType
from collections import defaultdict
from contextlib import suppress
from enum import IntEnum, auto
from typing import Tuple, Dict, Any, Iterator, Callable, Union, TypeVar, overload, MutableSequence, MutableMapping, cast

from reactives import Reactive

try:
    from graphlib import TopologicalSorter
except ImportError:  # pragma: no cover
    from graphlib_backport import TopologicalSorter  # type: ignore[no-redef]  # pragma: no cover

try:
    from typing_extensions import Self, TypeAlias
except ImportError:  # pragma: no cover
    from typing import Self, TypeAlias  # type: ignore  # pragma: no cover


class TriggerOrigin(IntEnum):
    # A trigger originating from outside a reactive or reactor controller.
    EXTERNAL = auto()
    # A trigger originating from inside a reactor controller. This will skip the reactor controller's on-trigger event
    # handler.
    INTERNAL = auto()


class _ReactorChain:
    def __init__(self) -> None:
        self._target_reactor_graph: MutableMapping[ReactorGraphNode, MutableSequence[ReactorGraphNode]] = defaultdict(list)
        self._target_nodes: Iterator[ReactorGraphNode] | None = None

    def update(
            self,
            source_reactor_controller: ReactorController,
            origin: TriggerOrigin = TriggerOrigin.EXTERNAL,
    ) -> None:
        self._target_nodes = None
        for source_reactor, target_reactor in self._resolve_edges(None, source_reactor_controller, origin):
            if source_reactor is not None:
                self._target_reactor_graph[target_reactor].append(source_reactor)

    def _resolve_edges(
            self,
            source_node: ReactorGraphNode | None,
            target_node: ReactorGraphNode,
            origin: TriggerOrigin = TriggerOrigin.EXTERNAL,
    ) -> Iterator[Tuple[ReactorGraphNode | None, ReactorGraphNode]]:
        yield source_node, target_node
        if isinstance(target_node, ReactorController):
            yield from self._resolve_reactor_controller_edges(target_node, origin)

    def _resolve_reactor_controller_edges(
            self,
            target_node: ReactorController,
            origin: TriggerOrigin = TriggerOrigin.EXTERNAL,
    ) -> Iterator[Tuple[ReactorGraphNode | None, ReactorGraphNode]]:
        target_reactor_controller_reactors_source_node: ReactorGraphNode
        if origin is TriggerOrigin.INTERNAL:
            target_reactor_controller_reactors_source_node = target_node
        else:
            yield target_node, target_node._on_trigger
            target_reactor_controller_reactors_source_node = target_node._on_trigger
        for target_reactor_controller_reactor in target_node._reactors:
            yield from self._resolve_edges(
                target_reactor_controller_reactors_source_node,
                target_reactor_controller_reactor,
            )

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Reactor:
        # Rebuild the reactors if they were updated.
        if self._target_nodes is None:
            self._target_nodes = cast(Iterator[ReactorGraphNode], TopologicalSorter(self._target_reactor_graph).static_order())

        target_reactor = next(self._target_nodes)

        # Remove the reactor from the graph.
        with suppress(KeyError):
            del self._target_reactor_graph[target_reactor]
        for source_reactors in self._target_reactor_graph.values():
            with suppress(ValueError):
                source_reactors.remove(target_reactor)

        # Skip reactor controllers, which are kept for graph resolution, but are not reactors themselves.
        if isinstance(target_reactor, ReactorController):
            return self.__next__()
        return target_reactor

    def trigger(
            self,
            source_reactor_controller: ReactorController,
            origin: TriggerOrigin = TriggerOrigin.EXTERNAL,
    ) -> None:
        self.update(source_reactor_controller, origin)
        for target_reactor in self:
            target_reactor()


class _ReactorChainTrigger:
    _current: _ReactorChain | None = None

    @classmethod
    def trigger(
            cls,
            source_reactor_controller: ReactorController,
            origin: TriggerOrigin = TriggerOrigin.EXTERNAL,
    ) -> None:
        if cls._current:
            cls._current.update(source_reactor_controller, origin)
        else:
            cls._current = _ReactorChain()
            try:
                cls._current.trigger(source_reactor_controller, origin)
            finally:
                cls._current = None


class ReactorController:
    def __init__(self) -> None:
        self.__reactors: MutableSequence[ReactorGraphNode | ReferenceType[ReactorGraphNode]] = []
        self._dependencies: MutableSequence[ReactorController] = []

    def __call__(self, *reactors: ResolvableReactor) -> None:
        self.react(*reactors)

    def __copy__(self) -> Self:
        copied = self.__class__.__new__(self.__class__)
        copied.__reactors = copy.copy(self.__reactors)
        return copied

    def __getstate__(self) -> Dict[str, Any]:
        return {
            '__reactors': self.__reactors,
            '_dependencies': self._dependencies,
        }

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.__reactors = state['__reactors']
        self._dependencies = state['_dependencies']

    @property
    def _reactors(self) -> Iterator[ReactorGraphNode]:
        yield from filter(None, map(
            self._unweakref,  # type: ignore[arg-type]
            self.__reactors,
        ))

    def trigger(self) -> None:
        _ReactorChainTrigger.trigger(self)

    def _trigger(self) -> None:
        _ReactorChainTrigger.trigger(self, TriggerOrigin.INTERNAL)

    def _on_trigger(self) -> None:
        pass

    def _weakref(self, reactor: ReactorGraphNodeT, callback: Callable[[ReferenceType[ReactorGraphNodeT]], Any]) -> ReferenceType[ReactorGraphNodeT]:
        if inspect.ismethod(reactor):
            return weakref.WeakMethod(
                reactor,  # type: ignore[arg-type]
                callback,  # type: ignore[arg-type]
            )
        # weakref.proxy is not hashable, so we use weakref.ref and dereference it ourselves.
        return weakref.ref(reactor, callback)

    def _unweakref(self, reference: ReactorGraphNodeT | ReferenceType[ReactorGraphNodeT]) -> ReactorGraphNodeT | None:
        if isinstance(reference, weakref.ref):
            return reference()
        return reference

    def _resolve_reactor(self, reactor: ResolvableReactor) -> ReactorGraphNode:
        if isinstance(reactor, Reactive):
            return reactor.react
        return reactor

    def _append_reactor(self, reactor: ReactorGraphNode | ReferenceType[ReactorGraphNode]) -> None:
        if reactor not in self.__reactors:
            self.__reactors.append(reactor)

    def react(self, *reactors: ResolvableReactor) -> None:
        for reactor in reactors:
            self._append_reactor(self._resolve_reactor(reactor))

    def react_weakref(self, *reactors: ResolvableReactor) -> None:
        for reactor in reactors:
            self._append_reactor(self._weakref(self._resolve_reactor(reactor), self._shutdown_reactor))

    def shutdown(self, *reactors: ResolvableReactor) -> None:
        if not reactors:
            self.__reactors.clear()
            return

        for reactor in reactors:
            self._shutdown_reactor(reactor)

    def _shutdown_reactor(self, reactor: ResolvableReactor) -> None:
        reactor = self._resolve_reactor(reactor)
        # To prevent the list from reindexing the values we still have to remove, compare reactors in reverse.
        for i, self_reactor in reversed(list(enumerate(map(
            self._unweakref,  # type: ignore[arg-type]
            self.__reactors,
        )))):
            if reactor == self_reactor:
                del self.__reactors[i]


Reactor: TypeAlias = Callable[[], Any]
ReactorGraphNode: TypeAlias = Union[Reactor, ReactorController]
ReactorGraphNodeT = TypeVar('ReactorGraphNodeT', bound=ReactorGraphNode)
ReactorControllerT = TypeVar('ReactorControllerT', bound=ReactorController)
ResolvableReactorController: TypeAlias = Union[ReactorController, Reactive]
ResolvableReactorControllerT = TypeVar('ResolvableReactorControllerT', bound=ResolvableReactorController)
ResolvableReactor: TypeAlias = Union[Reactor, ResolvableReactorController]
ResolvableReactorT = TypeVar('ResolvableReactorT', bound=ResolvableReactor)


@overload
def resolve_reactor_controller(resolvable: Reactive) -> ReactorController:
    pass


@overload
def resolve_reactor_controller(resolvable: ReactorController) -> ReactorController:
    pass


def resolve_reactor_controller(resolvable: ResolvableReactorController) -> ReactorController:
    if isinstance(resolvable, ReactorController):
        return resolvable
    if isinstance(resolvable, Reactive):
        return resolvable.react
    raise ValueError(f'Cannot resolve the reactor controller for {resolvable}.')  # pragma: no cover


ExpectedCallCount = Union[int, Tuple[int, int], Tuple[int, None], Tuple[None, int]]


class AssertCallCountReactor:
    def __init__(self, expected_call_count: ExpectedCallCount):
        self._exact_expected_call_count: int | None
        self._minimum_expected_call_count: int | None
        self._maximum_expected_call_count: int | None
        if isinstance(expected_call_count, int):
            self._exact_expected_call_count = expected_call_count
            self._minimum_expected_call_count = expected_call_count
            self._maximum_expected_call_count = expected_call_count
        else:
            self._exact_expected_call_count = None
            self._minimum_expected_call_count, self._maximum_expected_call_count = expected_call_count
        self._actual_call_count = 0

    def __call__(self) -> None:
        self._actual_call_count += 1
        self._assert_maximum_call_count()

    def _assert(self, expectation_message: str) -> None:
        raise AssertionError(f'Failed asserting that a reactor ({self}) was {expectation_message}. Instead, it was actually called {self._actual_call_count} time(s).')

    def _assert_exact_call_count(self) -> None:
        if self._exact_expected_call_count is None:
            return
        if self._exact_expected_call_count == 0:
            if self._actual_call_count != 0:
                self._assert('never called')
        elif self._exact_expected_call_count == 1:
            if self._actual_call_count != 1:
                self._assert('called exactly once')
        else:
            if self._actual_call_count != self._exact_expected_call_count:
                self._assert(f'called exactly {self._exact_expected_call_count} times')

    def _assert_minimum_call_count(self) -> None:
        if self._minimum_expected_call_count is not None and self._actual_call_count < self._minimum_expected_call_count:
            self._assert(f'called at least {self._minimum_expected_call_count} time(s)')

    def _assert_maximum_call_count(self) -> None:
        if self._maximum_expected_call_count is not None and self._actual_call_count > self._maximum_expected_call_count:
            self._assert_exact_call_count()
            self._assert(f'called at most {self._maximum_expected_call_count} time(s)')

    def assert_call_count(self) -> None:
        self._assert_exact_call_count()
        self._assert_minimum_call_count()
        self._assert_maximum_call_count()
