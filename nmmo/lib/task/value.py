from abc import ABC, abstractmethod
from typing import Dict, List
from math import prod
from nmmo.lib.task.proposition import *

def implicitConstantDecorator(function):
    def wrapper(self,other):
        if (not isinstance(other,Value)):
            other = Constant(other)
        return function(self,other)
    return wrapper

class Value(ABC):
    '''
    Access a desired attribute concerning game state
    '''
    @abstractmethod
    def value(self, realm, entity) -> float:
        raise NotImplementedError

    def description(self) -> List:
        return self.__class__.__name__

    @implicitConstantDecorator
    def __lt__(self, other):
        return LT(self,other)
    @implicitConstantDecorator
    def __le__(self, other):
        return LE(self,other)
    @implicitConstantDecorator
    def __eq__(self, other):
        return EQ(self,other)
    @implicitConstantDecorator
    def __ne__(self, other):
        return NE(self,other)
    @implicitConstantDecorator
    def __gt__(self, other):
        return GT(self,other)
    @implicitConstantDecorator
    def __ge__(self, other):
        return GE(self,other)
    
    @implicitConstantDecorator
    def __add__(self,other):
        return Sum(self,other)
    @implicitConstantDecorator
    def __radd__(self,other):
        return Sum(self,other)
    @implicitConstantDecorator
    def __mul__(self,other):
        return Product(self,other)
    @implicitConstantDecorator
    def __rmul__(self,other):
        return Product(self,other)
    @implicitConstantDecorator
    def __sub__(self,other):
        return Sum(self, Product(other,Constant(-1)))
    @implicitConstantDecorator
    def __rsub__(self,other):
        return Sum(other, Product(self,Constant-1))


###############################################################

class Tick(Value):
    def value(self, realm, entity):
        return realm.tick

class Constant(Value):
    def __init__(self, value: float) -> None:
        super().__init__()
        self._value = value

    def value(self, realm, entity):
        return self._value

    def description(self) -> List:
        return [self._value]


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

class TargetValue(Value, ABC):
    def __init__(self, target: EntityTarget) -> None:
        self._target = target

    def description(self) -> List:
        return [super().description(), self._target.description()]
        
    @abstractmethod
    def value(self, realm, entity) -> bool:
        raise NotImplementedError

###############################################################
    
class Sum(Value):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return sum([op.value(realm, entity) for op in self._operands])
    
    def description(self) -> List:
        return ["+"] + [op.description() for op in self._operands]

class Product(Value):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return prod([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["x"] + [op.description() for op in self._operands]

class Max(Value):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return max([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["max"] + [op.description() for op in self._operands]

class Min(Value):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return min([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["min"] + [op.description() for op in self._operands]

###############################################################

class Alive(TargetValue):
    def __init__(self, target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity) -> int:
        return sum([realm.entity(a).alive for a in self._target.agents()])

class Health(TargetValue):
    def __init__(self,target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).resources.health.val for a in self._target.agents()])
        
class Gold(TargetValue):
    def __init__(self,target: EntityTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).inventory.gold.quantity.val for a in self._target.agents()])
        

class Group(TargetValue):
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
            for j in range(i,len(positions)):
                b = positions[j]
                if a[0] + self.distance <= b[0]:
                    break
                if a[1] + self.distance > b[0]:
                    temp += 1
            res = max(res,temp)
        return res

from nmmo.systems.skill import Mage, Range, Melee, Fishing, Herbalism, Prospecting, Carving, Alchemy
class SkillLevel(TargetValue, ABC):
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

class Harvest(TargetValue):
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

class InflictDamage(TargetValue):
    def __init__(self, target: EntityTarget, damage_type: int):
        super().__init__(target)
        self._damage_type = damage_type

    def value(self, realm, entity) -> int:
        # TODO(daveey) damage_type is ignored, needs to be added to entity.history
        return sum([
            realm.entity(a).history.damage_inflicted for a in self._target.agents()
        ])

    def description(self) -> List:
        return super().description() + [self._damage_type]

class EquipLevel(TargetValue):
    '''
    Returns maximum level of 'equipment' equipped on target, default 0
    '''

    def __init__(self, target: EntityTarget, equipment):
        super().__init__(target)
        self.equipment = equipment

    def value(self, realm, entity):
        raise NotImplementedError