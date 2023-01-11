from abc import ABC, abstractmethod
from typing import Dict, List
from math import prod

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

class VariableTarget:
    def __init__(self, name: str, agents: List[str]) -> None:
        self._name = name
        self._agents = agents

    def agents(self) ->  List[str]:
        return self._agents

    def description(self) -> List:
        return self._name

    def member(self, member):
        assert member < len(self._agents)
        return VariableTarget(f"{self.description()}.{member}", [self._agents[member]])

    def __str__(self):
        return self.description()

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
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return prod([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["x"] + [op.description() for op in self._operands]

class Max(Variable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return max([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["max"] + [op.description() for op in self._operands]

class Min(Variable):
    def __init__(self, *operands):
        super().__init__()
        self._operands = operands
    
    def value(self, realm, entity):
        return min([op.value(realm, entity) for op in self._operands])

    def description(self) -> List:
        return ["min"] + [op.description() for op in self._operands]

###############################################################

class Alive(TargetVariable):
    def __init__(self, target: VariableTarget):
        super().__init__(target)
    
    def value(self, realm, entity) -> int:
        return sum([realm.entity(a).alive for a in self._target.agents()])

class Health(TargetVariable):
    def __init__(self,target: VariableTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).resources.health.val for a in self._target.agents()])
        
class Gold(TargetVariable):
    def __init__(self,target: VariableTarget):
        super().__init__(target)
    
    def value(self, realm, entity):
        return sum([realm.entity(a).inventory.gold.quantity.val for a in self._target.agents()])
        

class Group(TargetVariable):
    '''
    Maximum group size within a bounding box of (distance x distance)
    '''
    def __init__(self,target: VariableTarget, distance : int):
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
class SkillLevel(TargetVariable, ABC):
    def __init__(self, target: VariableTarget, skill):
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


# TODO: Implementation of below incomplete

class Harvest(TargetVariable):
    '''
    target: The team that is completing the task. Any agent may complete
    resource: lib.material to harvest
    level: minimum material level to harvest
    '''
    def __init__(self, target: VariableTarget, resource, level: int):
        super().__init__(target)
        self.resource = resource
        self.level = level

    def value(Self, realm, entity):
        # TODO(mark) need to add into entity.history 
        raise NotImplementedError

class InflictDamage(TargetVariable):
    def __init__(self, target: VariableTarget, damage_type: int):
        super().__init__(target)
        self._damage_type = damage_type

    def value(self, realm, entity) -> int:
        # TODO(daveey) damage_type is ignored, needs to be added to entity.history
        return sum([
            realm.entity(a).history.damage_inflicted for a in self._target.agents()
        ])

    def description(self) -> List:
        return super().description() + [self._damage_type]

class EquipLevel(TargetVariable):
    '''
    Returns maximum level of 'equipment' equipped on target, default 0
    '''

    def __init__(self, target: VariableTarget, equipment):
        super().__init__(target)
        self.equipment = equipment

    def value(self, realm, entity):
        raise NotImplementedError