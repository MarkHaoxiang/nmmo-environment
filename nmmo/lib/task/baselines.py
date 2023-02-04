from nmmo.lib.task.proposition import *
from nmmo.lib.task.value import *

'''
Contains a set of standard baselines tasks
'''

'''
TODO(discussion)
Description -> return type
'''

class Attack(Task):
  def __init__(self, target: EntityTarget, damage_type: int, quantity: int) -> None:
    super().__init__()
    self._task = InflictDamage(target,damage_type) > quantity
    self._target = target
    self._damage_type = damage_type
    self._quantity = quantity

  def evaluate(self, realm, entity) -> bool:
    return self._task.evaluate(realm,entity)

class Eliminate(Task):
  def __init__(self, target: EntityTarget, num_steps: int) -> None:
    super().__init__()
    self._task = (num_steps > Tick()) & (Alive(target) == 0)
    self._num_steps = num_steps
    self._target = target

  def evaluate(self, realm, entity) -> bool:
    return self._task.evaluate(realm,entity)
  

class Defend(Task):
  def __init__(self, target: EntityTarget, num_steps: int) -> None:
    super().__init__()
    self._task = (num_steps < Tick()) & (Alive(target) < len(target.agents()))
    self._num_steps = num_steps
    self._target = target

  def evaluate(self, realm, entity) -> bool:
    return self._task.evaluate(realm,entity)

class Hoard(Task):
  def __init__(self, target: EntityTarget, gold: int) -> None: 
    super().__init__()
    self._task = Gold(target) > gold
    self._target = target
    self._gold = gold
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)

class Achieve(Task):
  def __init__(self,target: EntityTarget, skill, level) -> None:
    super().__init__()
    self._task = SkillLevel(target,skill) > level
    self._target = target
    self._skill = skill
    self._level = "low"
    if level >= 4:
      self._level = "medium"
    elif level >= 7:
      self._level = "high"
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)

class Harvest(Task):
  def __init__(self, target: EntityTarget, resource, level, amount: int) -> None: 
    super().__init__()
    self._task = Resource(target,resource,level) > amount
    self._target = target
    self._level = level
    self._resource = resource
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)

class Assemble(Task):
  def __init__(self, target: EntityTarget, num_agents, distance=5) -> None:
    super().__init__()
    self._task = Group(target,distance) >= num_agents
    self._num_agents = str(num_agents)
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)

class Spread(Task):
  def __init__(self, target: EntityTarget, distance) -> None:
    super().__init__()
    self._task = Group(target,distance) == 1
    self._distance = distance
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)

class Equip(Task):
  def __init__(self, target: EntityTarget, equipment, level) -> None:
    super().__init__()
    self._task = EquipmentLevel(target, equipment) > level
    self._equipment = equipment
    self._level = level
  
  def evaluate(self, realm, entity):
    return self._task.evaluate(realm,entity)