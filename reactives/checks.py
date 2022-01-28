from typing import Type

from reactives.controller import ReactorController


def assert_reactive(subject, controller_type: Type[ReactorController] = ReactorController) -> None:
    if not hasattr(subject, 'react'):
        raise AssertionError(f'{subject} is not reactive: {subject}.react does not exist.')
    if not isinstance(subject.react, controller_type):
        raise AssertionError(f'{subject} is not reactive: {subject}.react is not an instance of {controller_type}.')


def is_reactive(subject, controller_type: Type[ReactorController] = ReactorController) -> bool:
    return hasattr(subject, 'react') and isinstance(subject.react, controller_type)
