from abc import ABC, abstractmethod
from typing import List
import json

'''
TODO(mark) optimization

1. check whether a proposition can change during an episode by adding limit identifiers to variables
2. the current method of obtaining a description through list addition is inefficient
'''

class Proposition(ABC):
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

class AND(Proposition):
  def __init__(self, *propositions: Proposition) -> None:
    super().__init__()
    assert len(propositions)
    self._propositions = propositions

  def evaluate(self, realm, entity) -> bool:
    return all([t.evaluate(realm, entity) for t in self._propositions])

  def description(self) -> List:
    return ["AND"] + [t.description() for t in self._propositions]

class OR(Proposition):
  def __init__(self, *propositions: Proposition) -> None:
    super().__init__()
    assert len(propositions)
    self._propositions = propositions

  def evaluate(self, realm, entity) -> bool:
    return any([t.evaluate(realm, entity) for t in self._propositions])

  def description(self) -> List:
    return ["OR"] + [t.description() for t in self._propositions]

class NOT(Proposition):
  def __init__(self, proposition: Proposition) -> None:
    super().__init__()
    self._proposition = proposition

  def evaluate(self, realm, entity) -> bool:
    return not self._proposition.evaluate(realm, entity)

  def description(self) -> List:
    return ["NOT"] +  [self._proposition.description()] 

###############################################################

class GEQ(Proposition):
    def __init__(self, lhs ,rhs) -> None:
       super().__init__()
       self._lhs, self._rhs = lhs, rhs

    def evaluate(self, realm, entity) -> bool:
       return self._lhs.value(realm,entity) >= self._rhs.value(realm,entity)

    def description(self) -> List:
       return ['GEQ'] + self._lhs.description() + self._rhs.description()