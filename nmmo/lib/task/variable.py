from abc import ABC, abstractmethod
from typing import Dict, List

class Variable:
    '''
    Access a desired attribute concerning game state
    '''
    @abstractmethod
    def value(self, realm, entity) -> int:
        raise NotImplementedError

    def description(self) -> List:
        return self.__class__.__name__

###############################################################

class Tick(Variable):
    def value(self, realm, entity):
        return realm.tick

class Constant(Variable):
    def __init__(self, value: int) -> None:
        super().__init__()
        self._value = value

    def value(self, realm, entity):
        return self._value

    def description(self) -> List:
        return [self._value]

###############################################################

class VariableTarget(object):
    def __init__(self, name: str, agents: List[str]) -> None:
        self._name = name
        self._agents = agents

    def agents(self) ->  List[int]:
        return self._agents

    def description(self) -> List:
        return self._name

    def member(self, member):
        assert member < len(self._agents)
        return VariableTarget(f"{self.description()}.{member}", [self._agents[member]])

class TargetVariable(Variable, ABC):
    def __init__(self, target: VariableTarget) -> None:
        self._target = target

    def description(self) -> List:
        return [super().description(), self._target.description()]

    @abstractmethod
    def value(self, realm, entity) -> bool:
        raise NotImplementedError

###############################################################
    
class Sum(Variable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return sum([op.value(realm, entity) for op in self._operands])
    
    def description(self) -> List:
        return ["+"] + [op.description() for op in self._operands]

class Product(Variable):
    pass

class Max(Variable):
    pass

class Min(Variable):
    pass

###############################################################

class InflictDamage(TargetVariable):
    def __init__(self, target: VariableTarget, damage_type: int):
        super().__init__(target)
        self._damage_type = damage_type

    def value(self, realm, entity) -> int:
        # TODO(daveey) damage_type is ignored, needs to be added to entity.history
        return sum([
            realm.players[a].history.damage_inflicted for a in self._target.agents()
        ])

    def description(self) -> List:
        return ['Damage'] + super().description() + [self._damage_type]

class Alive(TargetVariable):
    def __init__(self, target: VariableTarget):
        super().__init__(target)
    
    def value(self, realm, entity) -> int:
        return sum([realm.players[a].alive for a in self._target.agents()])

    def description(self) -> List:
        return ['Alive'] + super().description()

class Health(TargetVariable):
    pass

class Gold(TargetVariable):
    pass

class Group(TargetVariable):
    pass

class Level(TargetVariable):
    pass

class Harvest(TargetVariable):
    pass
