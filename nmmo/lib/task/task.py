from typing import Dict, List

from nmmo.lib.task.proposition import *
from nmmo.lib.task.value import *

'''
Contains a set of standard baselines
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

  def description(self) -> List:
    return ["Attack"] + self._target.description() + [str(self._damage_type), str(self._quantity)]


class Defend(Task):
  def __init__(self, target: EntityTarget, num_steps: int) -> None:
    super().__init__()
    self._task = (num_steps < Tick()) & (Alive(target) < len(target.agents()))
    self._num_steps = num_steps
    self._target = target

  def evaluate(self, realm, entity) -> bool:
    return self._task.evaluate(realm,entity)

  def description(self) -> List:
    return ["Defend"] + self._target.description() + ['for', str(self._num_steps)]


################################################
#TODO(mark) move this out of tasks. define standard API for samplers
import random
from typing import Dict, List

class TeamHelper:
  def __init__(self, agents: List[int], num_teams: int) -> None:
    assert len(agents) % num_teams == 0
    self.team_size = len(agents) // num_teams
    self._teams = [
      list(agents[i * self.team_size : (i+1) * self.team_size]) 
      for i in range(num_teams)
    ]
    self._agent_to_team = {a: tid for tid, t in enumerate(self._teams) for a in t}

  def own_team(self, agent_id: int) -> EntityTarget:
    return EntityTarget("Team.Self", self._teams[self._agent_to_team[agent_id]])

  def left_team(self, agent_id: int) -> EntityTarget:
    return EntityTarget("Team.Left", self._teams[
      (self._agent_to_team[agent_id] -1) % len(self._teams)
    ])

  def right_team(self, agent_id: int) -> EntityTarget:
    return EntityTarget("Team.Right", self._teams[
      (self._agent_to_team[agent_id] + 1) % len(self._teams)
    ])

  def all(self) -> EntityTarget:
    return EntityTarget("All", list(self._agent_to_team.keys()))


class TaskSampler:
  def __init__(self) -> None:
    self._task_specs = []
    self._task_spec_weights = []
  
  def add_task_spec(self, task_class, param_space = [], weight: float = 1):
    self._task_specs.append((task_class, param_space))
    self._task_spec_weights.append(weight)

  def sample(self, 
             min_clauses: int = 1, 
             max_clauses: int = 1,
             min_clause_size: int = 1,
             max_clause_size: int = 1,
             not_p: float = 0.0) -> Task:
    
    clauses = []
    for c in range(0, random.randint(min_clauses, max_clauses)):
      task_specs = random.choices(
        self._task_specs, 
        weights = self._task_spec_weights,
        k = random.randint(min_clause_size, max_clause_size)
      )
      tasks = []
      for task_class, task_param_space in task_specs:
        task = task_class(*[random.choice(tp) for tp in task_param_space])
        if random.random() < not_p:
          task = NOT(task)
        tasks.append(task)

      if len(tasks) == 1:
        clauses.append(tasks[0])
      else:
        clauses.append(AND(*tasks))

    if len(clauses) == 1:
      return clauses[0]

    return OR(*clauses)

  @staticmethod
  def create_default_task_sampler(team_helper: TeamHelper, agent_id: int):
    neighbors = [team_helper.left_team(agent_id), team_helper.right_team(agent_id)]
    own_team = team_helper.own_team(agent_id)
    team_mates = [own_team.member(m) for m in range(team_helper.team_size)]
    sampler = TaskSampler()

    sampler.add_task_spec(Attack, [neighbors + [own_team], [0, 1, 2], [0, 100, 1000]])
    sampler.add_task_spec(Defend, [team_mates, [512, 1024]])

    return sampler