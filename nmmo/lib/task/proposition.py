from abc import ABC, abstractmethod
from typing import List
import json

'''
TODO(mark) optimization

1. check whether a task can change during an episode by adding limit identifiers to variables
2. the current method of obtaining a description through list addition is inefficient
'''

class Task(ABC):
    '''
    Evaluates a state to a condition
    '''
    @abstractmethod
    def evaluate(self, realm, entity) -> bool:
      raise NotImplementedError

    def description(self) -> List:
      return self.__class__.__name__

    def to_string(self) -> str:
      return json.dumps(self.description())

###############################################################

class AND(Task):
  def __init__(self, *tasks: Task) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, realm, entity) -> bool:
    return all([t.evaluate(realm, entity) for t in self._tasks])

  def description(self) -> List:
    return ["AND"] + [t.description() for t in self._tasks]

class OR(Task):
  def __init__(self, *tasks: Task) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, realm, entity) -> bool:
    return any([t.evaluate(realm, entity) for t in self._tasks])

  def description(self) -> List:
    return ["OR"] + [t.description() for t in self._tasks]

class NOT(Task):
  def __init__(self, task: Task) -> None:
    super().__init__()
    self._task = task

  def evaluate(self, realm, entity) -> bool:
    return not self._task.evaluate(realm, entity)

  def description(self) -> List:
    return ["NOT"] +  [self._task.description()] 

###############################################################

class GEQ(Task):
    def __init__(self, lhs ,rhs) -> None:
       super().__init__()
       self._lhs, self._rhs = lhs, rhs

    def evaluate(self, realm, entity) -> bool:
       return self._lhs.value(realm,entity) >= self._rhs.value(realm,entity)

    def description(self) -> List:
       return ['GEQ'] + self._lhs.description() + self._rhs.description()