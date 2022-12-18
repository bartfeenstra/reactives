from __future__ import annotations

from typing import Any, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from reactives.reactor import ReactorController  # pragma: no cover


class Reactive:
    """
    Define a reactive type of any kind.
    """

    react: ReactorController

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


ReactiveT = TypeVar('ReactiveT', bound=Reactive)
