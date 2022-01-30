# Reactives

![Test status](https://github.com/bartfeenstra/reactives/workflows/Test/badge.svg) [![Code coverage](https://codecov.io/gh/bartfeenstra/reactives/branch/main/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/reactives) [![PyPI releases](https://badge.fury.io/py/reactives.svg)](https://pypi.org/project/reactives/) [![Supported Python versions](https://img.shields.io/pypi/pyversions/reactives.svg?logo=python&logoColor=FBE072)](https://pypi.org/project/reactives/) [![Recent downloads](https://img.shields.io/pypi/dm/reactives.svg)](https://pypi.org/project/reactives/) 

**Reactives** lets you write reactive code easily by making any of your objects and functions *reactive*. A reactive
can be *triggered* (`reactive.react.trigger()`), causing all its *reactors* to be called. A *reactor* is any callable
that takes no arguments, and you add it to a reactive via `reactive.react(reactor)`. When a reactive is triggered,
its reactors and its reactors' reactors are resolved, and each is called once in order.

**Reactives** uses a push-pull approach, meaning change notifications are pushed (reactors are called automatically and
won't have to pull for changes), but if a reactor needs to know what exactly changed, it must pull this information
itself.

## Usage
For any type to be reactive, it must have a `react` attribute containing a `reactives.ReactorController`. The most
common way to achieve this, is to decorate that type with `@reactives.reactive`. Some classes are provided that are
reactive and can be instantiated or inherited from directly.

### Custom classes
Decorate a class to make its individual instances reactive:
```python
from reactives import reactive

@reactive
class Apple:
    pass

apple = Apple()
apple.react(lambda: print('The apple got triggered!'))
apple.react.trigger()
# >>> "The apple got triggered!"
```

### Functions and methods 
Decorate a function:
```python
from reactives import reactive

@reactive
def apple():
    pass

apple.react(lambda: print('The apple got triggered!'))
apple.react.trigger()
# >>> "The apple got triggered!"
```

Decorate a method on a **reactive class**:
```python
from reactives import reactive

@reactive
class Apple:
    @reactive
    def apple(self):
        pass

apple = Apple()
apple.react.getattr('apple').react(lambda: print('The apple got triggered!'))
apple.react.getattr('apple').react.trigger()
# >>> "The apple got triggered!"
```
Reactive methods must be accessed through their instance, because `Apple.apple` would yield the class method.

Both functions and methods can be called automatically when they're triggered. This lets them set up something once, and
update that thing when they're triggered:
```python
from reactives import reactive

@reactive(on_trigger_call=True)
def warm_caches():
    """
    Warm the application's caches. When triggered (because the cached data has changed), re-warm the caches.
    """
    pass
```

### Properties
Decorate a property:
```python
from reactives import reactive

@reactive
class Apple:
    @reactive
    @property
    def apple(self) -> str:
        return 'I got you something!'

apple = Apple()
apple.react.getattr('apple').react(lambda: print('The apple got triggered!'))
apple.react.getattr('apple').react.trigger()
# >>> "The apple got triggered!"
```

If a property *deleter* is present, it will be called automatically when the property is triggered:
```python
from reactives import reactive

@reactive
class Apple:
    def __init__(self):
        self._computed_something = None

    @reactive
    @property
    def apple(self) -> str:
        if self._computed_something is None:
            self._computed_something = 'I got you something!'
        return self._computed_something

    @apple.deleter
    def apple(self)  -> None:
        self._computed_something = 'I got you nothing!'

apple = Apple()
print(apple.apple)
# >>> "I got you something!"
apple.react.getattr('apple').react().trigger()
print(apple.apple)
# >>> "I got you nothing!"
```

If you do not want automatic deletion, configure the property's `@reactive` decorator as such:
```python
from reactives import reactive

@reactive
class Apple:
    def __init__(self):
        self._computed_something = None

    @reactive(on_trigger_delete=False)
    @property
    def apple(self) -> str:
        if self._computed_something is None:
            self._computed_something = 'I got you something!'
        return self._computed_something

    @apple.deleter
    def apple(self)  -> None:
        self._computed_something = 'I got you nothing!'

apple = Apple()
print(apple.apple)
# >>> "I got you something!"
apple.react.getattr('apple').react().trigger()
print(apple.apple)
# >>> "I got you something!"
```

Property *setters* work exactly like with any other `property`:
```python
from reactives import reactive

@reactive
class Apple:
    def __init__(self):
        self._something = 'I got you something!'
        
    @reactive
    @property
    def apple(self) -> str:
        return self._something
    
    @apple.setter
    def apple(self, something: str):
        self._something = something

apple = Apple()
apple.react.getattr('apple').react(lambda: print('The apple got triggered!'))
apple.apple = 'I got you something else!'
# >>> "The apple got triggered!"
```

Values set through a property may themselves be reactive too. If they are, the property and the value are autowired, 
which means that the property becomes a reactor to the newly added value. As soon as the value is triggered,
so is the property. Therefore, if you want to react to any change to any of the values a property might have, all you
need to do is add your reactor to the property.

### Lists
`ReactiveList` is a reactive version of Python's built-in `list`. You can use it in exactly the same way as `list`:
```python
from reactives import ReactiveList

fruits = ReactiveList(['apple', 'banana'])
fruits.react(lambda: print('Look at all these delicious fruits!'))
fruits.append('orange')
# >>> "Look at all these delicious fruits!"
```

Values added to a `ReactiveList` may themselves be reactive too. If they are, the list and the value are autowired, 
which means that the list becomes a reactor to the newly added value. As soon as the value is triggered,
so is the list. Therefore, if you want to react to any change to any of the values in a `ReactiveList`, all you
need to do is add your reactor to the list.

### Dictionaries
`ReactiveDict` is a reactive version of Python's built-in `dict`. You can use it in exactly the same way as `dict`:
```python
from reactives import ReactiveDict

fruits = ReactiveDict(apple=5, banana=2)
fruits.react(lambda: print('Look at all these delicious fruits!'))
fruits['orange'] = 4
# >>> "Look at all these delicious fruits!"
```

Values added to a `ReactiveDict` may themselves be reactive too. If they are, the dictionary and the value are
autowired, which means that the dictionary becomes a reactor to the newly added value. As soon as the value is
triggered, so is the dictionary. Therefore, if you want to react to any change to any of the values in a `ReactiveDict`, 
all you  need to do is add your reactor to the dictionary.

### Autowiring
We've seen how [properties](#Properties), [lists](#Lists), and [dictionaries](#Dictionaries) autowire themselves to
their values. This is possible because properties, lists, and dictionaries know exactly which values move in and out of
them. In other cases, we use *scope*. Any reactive can start a scope with `reactives.scope.collect()` and collect all
reactives that are called or used during that scope window, and autowire itself to them. Conversely, any reactive can
register itself with the current scope (if there is one) with `reactives.scope.register*()`, and allow reactives
depending on it to autowire themselves. In fact, this is what properties do internally.

Autowiring means that as a developer, you won't need to worry about connecting the parts of your application most of the
time.

## Development
First, [fork and clone](https://guides.github.com/activities/forking/) the repository, and navigate to its root directory.

### Requirements
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
If you have [tox](https://pypi.org/project/tox/) installed on your machine, `tox --develop` will create the necessary
virtual environments and install all development dependencies. 

Alternatively, in any existing Python environment, run `./bin/build-dev`.

### Testing
In any existing Python environment, run `./bin/test`.

### Fixing problems automatically
In any existing Python environment, run `./bin/fix`.

## Contributions 🥳
Reactives is Free and Open Source Software. As such you are welcome to
[report bugs](https://github.com/bartfeenstra/reactives/issues) or
[submit improvements](https://github.com/bartfeenstra/reactives/pulls).

## Copyright & license
Reactives is copyright [Bart Feenstra](https://twitter.com/BartFeenstra/) and contributors, and released under the
[GNU General Public License, Version 3](./LICENSE.txt). In short, that means **you are free to use Reactives**, but **if you
distribute Reactives yourself, you must do so under the exact same license**, provide that license, and make your source
code available. 
