from abc import ABC, abstractmethod
from typing import List
import json

'''
Link up the abstract syntax tree.


TODO(mark) optimization

1. check whether a task can change during an episode by adding limit identifiers to variables
2. type checker for the task ast
3. equivalence?
'''

class Task(ABC):
  '''
  A task expression a mapping from game states to logic truth. 
  Representation is through an abstract language described below.

  There are two types: Task and Value.

    Task:
      A boolean expression evaluated from values. 
      Each subclass of Task represents a semantic expression  - either a logical connective between Task or an comparison on Value.

    Value:
      Numeric data obtained from the game state, or an operator combining values.
  '''

  @abstractmethod
  def evaluate(self, realm, entity) -> bool:
    '''
    Evaluates a state to a condition
    '''
    raise NotImplementedError

  def description(self) -> List:
    return self.__class__.__name__

  def to_string(self) -> str:
    return json.dumps(self.description())

  def __and__(self, other):
    return AND(self,other)
  def __or__(self, other):
    return OR(self,other)
  def __invert__(self):
    return NOT(self)

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
# Comparison

class Comparison(Task):
  def __init__(self, lhs, rhs):
    super().__init__()
    self._lhs, self._rhs = lhs,rhs

class LT(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) < self._rhs.value(realm,entity)

  def description(self) -> List:
    return ['Less than'] + self._lhs.description() + self._rhs.description()

class LE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) <= self._rhs.value(realm,entity)

  def description(self) -> List:
    return ['Less than or equal'] + self._lhs.description() + self._rhs.description()

class EQ(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) == self._rhs.value(realm,entity)

  def description(self) -> List:
    return ['Equal'] + self._lhs.description() + self._rhs.description()

class NE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) != self._rhs.value(realm,entity)

  def description(self) -> List:
    return ['Not equal'] + self._lhs.description() + self._rhs.description()

class GT(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) > self._rhs.value(realm,entity)

  def description(self) -> List:
    return ['Greater'] + self._lhs.description() + self._rhs.description()
  

class GE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
      super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
      return self._lhs.value(realm,entity) >= self._rhs.value(realm,entity)

  def description(self) -> List:
      return ['Greater than or equal'] + self._lhs.description() + self._rhs.description()


  