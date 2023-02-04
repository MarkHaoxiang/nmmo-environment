from abc import ABC, abstractmethod
from typing import List, Dict, TypedDict
import json

'''
Link up the abstract syntax tree.


TODO(mark) optimization

1. check whether a task can change during an episode by adding limit identifiers to variables
2. type checker for the task ast
3. equivalence
'''

class Task(ABC):
  '''
  A task expression a mapping from game states to logic truth. 
  Representation is through an abstract language described below.

  There are two types: Task and GameStateVariable.

    Task:
      A boolean expression evaluated from values. 
      Each subclass of Task represents a semantic expression  - either a logical connective between Task or an comparison on GameStateVariable.

    GameStateVariable: 
      Numeric data obtained from the game state, or an operator combining values.
  '''

  def __init__(self, *args, **kwargs):
    self._args : List = args
    self._kwargs : Dict = kwargs

  @abstractmethod
  def evaluate(self, realm, entity) -> bool:
    '''
    Evaluates a state to a condition
    '''
    raise NotImplementedError

  class SerializedTask(TypedDict):
    name: str
    args: List
    kwargs: Dict

  def description(self) -> SerializedTask:
    '''
    Partially serializes a task - protects against breaking the sandbox by overloading "evaluate"
    '''
    return {
      "name": self.__class__.__name__,
      "args": [lambda arg : (arg.description(),"subnode") if ("evaluate" in dir(arg) or "value" in dir(arg)) else (arg,"param") for arg in self._args],
      "kwargs": {k: (v.description(),"subnode") if "evaluate" in dir(v) or "value" in dir(v) else (v,"param") for k,v in self._kwargs.items()}
    }

  def __str__(self) -> str:
    return json.dumps(self.description())

  def __and__(self, other):
    return AND(self,other)
  def __or__(self, other):
    return OR(self,other)
  def __invert__(self):
    return NOT(self)
  def __rshift__(self,other):
    return IMPLY(self,other)

###############################################################

class TRUE(Task):
  def evaluate(self, realm, entity) -> bool:
    return True

class FALSE(Task):
  def evaluate(self, realm, entity) -> bool:
    return True

class AND(Task):
  def __init__(self, *tasks: Task) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, realm, entity) -> bool:
    return all([t.evaluate(realm, entity) for t in self._tasks])
class OR(Task):
  def __init__(self, *tasks: Task) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, realm, entity) -> bool:
    return any([t.evaluate(realm, entity) for t in self._tasks])

class NOT(Task):
  def __init__(self, task: Task) -> None:
    super().__init__()
    self._task = task

  def evaluate(self, realm, entity) -> bool:
    return not self._task.evaluate(realm, entity)

class IMPLY(Task):
  def __init__(self, p: Task, q: Task) -> None:
    super().__init__()
    self._p = p
    self._q = q
  
  def evaluate(self, realm, entity) -> bool:
    if self._p.evaluate(realm, entity) and not self._q.evaluate(realm, entity): 
      return False
    return True

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

class LE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) <= self._rhs.value(realm,entity)

class EQ(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) == self._rhs.value(realm,entity)

class NE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) != self._rhs.value(realm,entity)

class GT(Comparison):
  def __init__(self, lhs ,rhs) -> None:
    super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
    return self._lhs.value(realm,entity) > self._rhs.value(realm,entity)
  

class GE(Comparison):
  def __init__(self, lhs ,rhs) -> None:
      super().__init__(lhs,rhs)

  def evaluate(self, realm, entity) -> bool:
      return self._lhs.value(realm,entity) >= self._rhs.value(realm,entity)


  