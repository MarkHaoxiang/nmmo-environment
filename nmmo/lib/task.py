from __future__ import annotations
from dataclasses import dataclass
import copy, math

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

# Core API
class Task:
  '''Basic reward block

  Pass in an instance of Task to the Env to define the rewards of a environment.
  Each Task is assumed to be across entity
  '''
  def reward(self, gs: GameState) -> float:
    return 0

  def generate(self, agent):
    return copy.deepcopy(self)

  def __str__(self):
    return self.__class__.__name__

# Predicate tasks
class PredicateTask(Task):
  '''
  A boolean valued task
  '''
  def __init__(self, reward = 1, discount_factor = 0, maximum_completion=math.inf):
    super().__init__()
    self._discount_factor = discount_factor
    self._completion_count = 0 
    self._reward = reward
    self._maximum_completion = maximum_completion

  def reward(self, gs: GameState) -> float:
    if self._maximum_completion < self._completion_count:
        return 0
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
    
class ONCE(PredicateTask):
  def __init__(self, task: PredicateTask, reward = 1):
    super().__init__(reward=reward, discount_factor=0)
    self._task = task
  
  def evaluate(self, gs: GameState) -> bool:
    return self._task.evaluate(gs)

class REPEAT(PredicateTask):
  def __init__(self, task: PredicateTask, reward = 1):
    super().__init__(reward=reward, discount_factor=0)
    self._task = task

  def evaluate(self, gs: GameState) -> bool:
    return self._task.evaluate(gs)

class TRUE(PredicateTask):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
  def evaluate(self, gs) -> bool:
    return True

class FALSE(PredicateTask):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

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
  def __init__(self, task: PredicateTask, *args, **kwargs) -> None:
    super().__init__(*args,**kwargs)
    self._task = task

  def evaluate(self, gs) -> bool:
    return not self._task.evaluate(gs)

class IMPLY(PredicateTask):
  def __init__(self, p: PredicateTask, q: PredicateTask, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self._p = p
    self._q = q
  
  def evaluate(self, gs) -> bool:
    if self._p.evaluate(gs) and not self._q.evaluate(gs): 
      return False
    return True


# TeamTask
def team_task(task_class):
  '''Decorate a task to share state across a team
  '''
  class TeamTask(task_class):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self._args = args
      self._kwargs = kwargs
      self._team2task = {}

    def generate(self, agent):
      tid = agent.population_id.val
      if not tid in self._team2task:
        self._team2task[tid] = TeamTask(*self._args,**self._kwargs)
      return self._team2task[tid]

  return TeamTask