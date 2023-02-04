from abc import ABC, abstractmethod
from typing import Dict, List
from math import prod
from nmmo.lib.task.proposition import *

def ImplicitConstantDecorator(function):
    def wrapper(self,other):
        if (not isinstance(other,GameStateVariable)):
            other = Constant(other)
        return function(self,other)
    return wrapper

class GameStateVariable(ABC):
    '''
    Access a desired attribute concerning game state
    '''
    @abstractmethod
    def value(self, realm, entity) -> float:
        raise NotImplementedError

    def description(self) -> List:
        return self.__class__.__name__

    @ImplicitConstantDecorator
    def __lt__(self, other):
        return LT(self,other)
    @ImplicitConstantDecorator
    def __le__(self, other):
        return LE(self,other)
    @ImplicitConstantDecorator
    def __eq__(self, other):
        return EQ(self,other)
    @ImplicitConstantDecorator
    def __ne__(self, other):
        return NE(self,other)
    @ImplicitConstantDecorator
    def __gt__(self, other):
        return GT(self,other)
    @ImplicitConstantDecorator
    def __ge__(self, other):
        return GE(self,other)
    
    @ImplicitConstantDecorator
    def __add__(self,other):
        return Sum(self,other)
    @ImplicitConstantDecorator
    def __radd__(self,other):
        return Sum(self,other)
    @ImplicitConstantDecorator
    def __mul__(self,other):
        return Product(self,other)
    @ImplicitConstantDecorator
    def __rmul__(self,other):
        return Product(self,other)
    @ImplicitConstantDecorator
    def __sub__(self,other):
        return Sum(self, Product(other,Constant(-1)))
    @ImplicitConstantDecorator
    def __rsub__(self,other):
        return Sum(other, Product(self,Constant-1))


###############################################################

# TODO(mark) is this really needed?
class Tick(GameStateVariable):
    def value(self, realm, entity):
        return realm.tick

class Constant(GameStateVariable):
    def __init__(self, value: float) -> None:
        super().__init__()
        self._value = value

    def value(self, realm, entity):
        return self._value
class Apply(GameStateVariable):

    def __init__(self, fn, *operands) -> None:
        super().__init__()
        self._fn = fn
        self._operands = operands

    def value(self, realm, entity):
        result = self._fn(*[x.value(realm,entity) for x in self._operands])
        assert isinstance(result,float)
        return result

###############################################################

#TODO(mark) Discuss - is evaluate/value guaranteed to be called each turn
class StatefulVariable(GameStateVariable, ABC):
    def __init__(self):
        self.reset()

    @abstractmethod
    def reset(self):
        raise NotImplementedError

class RunningTotal(StatefulVariable):
    def __init__(self,operand):
        super().__init()
        self._operand = operand

    def reset(self):
        self._running_total = 0

    def value(self, realm, entity):
        self._running_total += self._operand.value(realm, entity)
        return self._running_total

class PreviousValue(StatefulVariable):
    def __init__(self, operand):
        super().__init()
        self._operand = operand
    
    def reset(self):
        self._v = 0
    
    def value(self, realm, entity):
        self._v = self._operand.value(realm, entity)
        return self._v

###############################################################

class EntityTarget:
    def __init__(self, name: str, agents: List[str]) -> None:
        self._name = name
        self._agents = agents

    def agents(self) ->  List[str]:
        return self._agents

    def description(self) -> List:
        return self._name

    def member(self, member):
        assert member < len(self._agents)
        return EntityTarget(f"{self.description()}.{member}", [self._agents[member]])

    def __str__(self):
        return self.description()

class TargetGameStateVariable(GameStateVariable, ABC):
    def __init__(self, target: EntityTarget) -> None:
        self._target = target
        
    @abstractmethod
    def value(self, realm, entity) -> bool:
        raise NotImplementedError

###############################################################
    
class Sum(GameStateVariable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return sum([op.value(realm, entity) for op in self._operands])

class Product(GameStateVariable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return prod([op.value(realm, entity) for op in self._operands])
class Modulus(GameStateVariable):
    def __init__(self, a: GameStateVariable, b: GameStateVariable):
        super().__init__()
        self._a = a
        self._b = b
    
    def value(self, realm, entity):
        return self._a.value(realm, entity) % self._a.value(realm, entity)

    def description(self) -> List:
        return ["%"] + [self._a.description(), self._b.description()]

class Max(GameStateVariable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return max([op.value(realm, entity) for op in self._operands])

class Min(GameStateVariable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return min([op.value(realm, entity) for op in self._operands])

###############################################################

class Alive(TargetGameStateVariable):
    def __init__(self, target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity) -> int:
        return sum([realm.entity(a).alive for a in self._target.agents()])

class Health(TargetGameStateVariable):
    def __init__(self,target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).resources.health.val for a in self._target.agents()])
        
class Gold(TargetGameStateVariable):
    def __init__(self,target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).inventory.gold.quantity.val for a in self._target.agents()])
        
class Group(TargetGameStateVariable):
    '''
    Maximum group size within a bounding box of (distance x distance)
    '''
    def __init__(self,target: EntityTarget, distance : int):
        super().__init__(target)
        self.distance = distance

    def value(self, realm, entity):
        positions = [realm.entity(a).pos for a in self._target.agents()]
        positions.sort() # Sort by r
        res = 1
        for i,a in enumerate(positions):
            temp = 1
            for j in range(i+1,len(positions)):
                b = positions[j]
                if a[0] + self.distance <= b[0]:
                    break
                if a[1] + self.distance > b[0]:
                    temp += 1
            res = max(res,temp)
        return res

from nmmo.systems.skill import Mage, Range, Melee, Fishing, Herbalism, Prospecting, Carving, Alchemy
class SkillLevel(TargetGameStateVariable, ABC):
    def __init__(self, target: EntityTarget, skill):
        super().__init__(target)
        self.skill = skill
    
    def value(self, realm, entity):
        class2func = {
            Mage: lambda player: player.skills.mage.level.val,
            Range: lambda player: player.skills.mage.level.val,
            Melee: lambda player: player.skills.mage.level.val,
            Fishing: lambda player: player.skills.mage.level.val,
            Herbalism: lambda player: player.skills.mage.level.val,
            Prospecting: lambda player: player.skills.mage.level.val,
            Carving: lambda player: player.skills.mage.level.val,
            Alchemy: lambda player: player.skills.mage.level.val,
        }

        return max([class2func[self.skill](realm.entity(a)) for a in self._target.agents()])


# TODO(mark): Implementation of below incomplete

class Resource(TargetGameStateVariable):
    '''
    target: The team that is completing the task. Any agent may complete
    resource: lib.material to harvest
    level: minimum material level to harvest
    '''
    def __init__(self, target: EntityTarget, resource, level: int):
        super().__init__(target)
        self.resource = resource
        self.level = level

    def value(Self, realm, entity):
        # TODO(mark) need to add into entity.history 
        raise NotImplementedError

class InflictDamage(TargetGameStateVariable):
    def __init__(self, target: EntityTarget, damage_type: int):
        super().__init__(target)
        self._damage_type = damage_type

    def value(self, realm, entity) -> int:
        # TODO(daveey) damage_type is ignored, needs to be added to entity.history
        return sum([
            realm.entity(a).history.damage_inflicted for a in self._target.agents()
        ])


class EquipmentLevel(TargetGameStateVariable):
    '''
    Returns maximum level of 'equipment' equipped on target, default 0
    '''

    def __init__(self, target: EntityTarget, equipment):
        super().__init__(target)
        self.equipment = equipment

    def value(self, realm, entity):
        raise NotImplementedError