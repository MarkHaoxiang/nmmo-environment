from __future__ import annotations
import abc
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

class TeamHelper():
  def __init__(self, agents: List[int], num_teams: int) -> None:
    assert len(agents) % num_teams == 0
    self.team_size = len(agents) // num_teams
    self._teams = [
      list(agents[i * self.team_size : (i+1) * self.team_size])
      for i in range(num_teams)
    ]
    self._agent_to_team = {a: tid for tid, t in enumerate(self._teams) for a in t}

  def own_team(self, agent_id: int):
    return self._teams[self._agent_to_team[agent_id]]

  def left_team(self, agent_id: int):
    return self._teams[(self._agent_to_team[agent_id] -1) % len(self._teams)]

  def right_team(self, agent_id: int):
    return self._teams[(self._agent_to_team[agent_id] + 1) % len(self._teams)]

  def all_agents(self):
    return self._agent_to_team.keys()
  
  def all_teams(self):
    return list(set(self._agent_to_team.values()))

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

    # Global variable
    self.tick = realm.tick

    # Entity Specific
    self.team_helper = TeamHelper([agent.ent_id for agent in realm.players.values()], config.PLAYER_N // config.PLAYER_TEAM_SIZE)

    self.agents: Dict[int, AgentVariable] = {}
    for agent in realm.players.values():
      self.agents[agent.ent_id] = AgentVariable(agent.resources.health.val, (agent.row, agent.col))

    self.teams: Dict[int, List[List[AgentVariable]]] = {}
    for tid in self.team_helper.all_teams():
      self.teams[tid] = []
    for eid, agent_variable in self.agents.items():
      self.teams[self.team_helper._agent_to_team[eid]].append(agent_variable)
    
  def generate(self, eid: int) -> GameState:
    all_teams = copy.deepcopy(self.teams)
    tid = self.team_helper._agent_to_team[eid]
    return GameState(
      tick = self.tick, 
      agent = copy.deepcopy(self.agents[eid]), 
      team = all_teams.pop(tid), 
      opponents = all_teams)

'''
Pass in an instance of Task to the Env to define the rewards of a environment.
Each Task is assumed to be across entity
'''
class Task:

  def reward(self, gs: GameState) -> float:
    return 0

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