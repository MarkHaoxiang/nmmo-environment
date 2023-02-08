from __future__ import annotations
from dataclasses import dataclass
import copy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from typing import List, Tuple
  from typing import Tuple, Dict, List
  from nmmo.core.realm import Realm
  from nmmo.core.config import Config

# pylint: disable=abstract-method, super-init-not-called

# API

'''
Layer between realm and rewards, releasing a subset of preselected variables and state. 

1. Initialize GameStateGenerator from realm
2. Pass in Entity to GameStateGenerator to create GameState
3. Pass GameState through Task to obtain reward
'''

@dataclass
class AgentVariable:
  health: int
  position: Tuple[int,int]

@dataclass
class GameState:
  tick: int
  agent: AgentVariable
  team: List[AgentVariable]
  opponents: List[List[AgentVariable]] 

class GameStateGenerator:
  def __init__(self, realm: Realm, config: Config):
    # Entity
    self.agents: Dict[int, AgentVariable] = {}
    for agent in realm.players.values():
      self.agents[agent.ent_id] = AgentVariable(agent.resources.health.val, (agent.row.val, agent.col.val))
      
    # Team
    self.eid2tid={}
    self.teams: Dict[int, List[List[AgentVariable]]] = {}
    for agent in realm.players.values():
      self.eid2tid[agent.ent_id] = agent.population_id.val
      self.teams[agent.population_id.val] = []
    for agent in realm.players.values():
      self.teams[agent.population_id.val].append(self.agents[agent.ent_id])

    # Global variable
    self.tick = realm.tick
    
  def generate(self, eid: int) -> GameState:
    tid = self.eid2tid[eid]
    return GameState(
      tick = self.tick, 
      agent = self.agents[eid], 
      team = self.teams[tid], 
      opponents = self.teams)

'''
Pass in an instance of Task to the Env to define the rewards of a environment.
Each Task is assumed to be across entity
'''
class Task:

  def reward(self, gs: GameState) -> float:
    return 0

  def generate(self):
    return copy.deepcopy(self)

  def __str__(self):
    return self.__class__.__name__

'''
A mapping from GameState to true/false
'''
class PredicateTask(Task):
  def __init__(self, reward = 1, discount_factor = 0):
    self._discount_factor = discount_factor
    self._completion_count = 0 
    self._reward = reward

  def reward(self, gs: GameState) -> float:
    if self.evaluate(gs):
      self._completion_count += 1
      return self._reward * self._discount_factor ** (self._completion_count-1)
    return 0

  def evaluate(self, gs: GameState) -> bool:
    raise NotImplementedError

  def __and__(self, other):
    return AND(self,other)
  def __or__(self, other):
    return OR(self,other)
  def __invert__(self):
    return NOT(self)
  def __rshift__(self,other):
    return IMPLY(self,other)

# Baselines

class ONCE(PredicateTask):
  def __init__(self, reward = 1):
    super().__init__(reward=reward, discount_factor=0)

class REPEAT(PredicateTask):
  def __init__(self, reward = 1):
    super().__init__(reward=reward, discount_factor=1)

class TRUE(PredicateTask):
  def evaluate(self, gs) -> bool:
    return True

class FALSE(PredicateTask):
  def evaluate(self, gs) -> bool:
    return False

class AND(PredicateTask):
  def __init__(self, *tasks: PredicateTask) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, gs) -> bool:
    return all([t.evaluate(gs) for t in self._tasks])
class OR(PredicateTask):
  def __init__(self, *tasks: PredicateTask) -> None:
    super().__init__()
    assert len(tasks)
    self._tasks = tasks

  def evaluate(self, gs) -> bool:
    return any([t.evaluate(gs) for t in self._tasks])

class NOT(PredicateTask):
  def __init__(self, task: PredicateTask) -> None:
    self._task = task

  def evaluate(self, gs) -> bool:
    return not self._task.evaluate(gs)

class IMPLY(PredicateTask):
  def __init__(self, p: PredicateTask, q: PredicateTask) -> None:
    super().__init__()
    self._p = p
    self._q = q
  
  def evaluate(self, gs) -> bool:
    if self._p.evaluate(gs) and not self._q.evaluate(gs): 
      return False
    return True