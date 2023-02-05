# pylint: disable=redefined-outer-name,super-init-not-called

from typing import List
from pettingzoo.utils.env import AgentID

import unittest

import nmmo
from nmmo.lib import task
from nmmo.core.realm import Realm
from nmmo.entity.entity import Entity
from scripted.baselines import Sleeper


class Success(task.Task):
  def completed(self) -> bool:
    return True

class Failure(task.Task):
  def completed(self) -> bool:
    return False

# Currently supports single task to all agents
#     without using the Diary and Achievement classes
# TODO: multiple tasks, different reward amount, diffenent task assignment
class TaskWrapper(nmmo.Env):
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
  
  def reset(self, task: task.Task = None, map_id=None, seed=None, options=None):
    """OpenAI Gym API reset function
    Loads a new game map and returns initial observations
    Currently, assigns the same task set to all agents

    Args:
    task: A SINGLE task to assign to all agents.
    map_id: Map index to load. Selects a random map by default

    Returns:
    observations, as documented by _compute_observations()
    """
    self._init_random(seed)
    self.realm.reset(map_id)

    # assign the task_set for each player
    if task:
      for agent in self.realm.players.values():
          agent.tasks = task

    self.obs = self._compute_observations()

    return {a: o.to_gym() for a,o in self.obs.items()}

  def _task_completion(self): #, obs, rew, done, info):
    """
    Implement this function to indicate whether the selected task has been completed.
    This can be determined using the observation, rewards, done, info or internal values
    from the environment. Intended to be used for automatic curricula.

    dones:
        A dictionary of agent done booleans of format::

          {
              agent_1: done_1,
              agent_2: done_2,
              ...
          }
    """
    done = {}
    for eid, ent in self.realm.players.items():
      # TODO: tasks must refer to GameStateVar instead of realm
      #       tasks should be able to use team observation? 
      done[eid] = ent.tasks.completed()

    return done

  def _encode_goal(self):
    """
    Implement this method to indicate which task is selected to the agent.
    Returns: Numpy array encoding the goal.
    """
    return None  

  def _compute_rewards(self, agents: List[AgentID] = None):
    '''Computes the reward for the specified agent

    Override this method to create custom reward functions. You have full
    access to the environment state via self.realm. Our baselines do not
    modify this method; specify any changes when comparing to baselines

    Args:
        player: player object

    Returns:
        reward:
          The reward for the actions on the previous timestep of the
          entity identified by ent_id.
    '''
    infos = {}
    rewards = {}

    for agent_id in agents:
      infos[agent_id] = {}
      agent = self.realm.players.get(agent_id)

      if agent is None:
        rewards[agent_id] = -1
        continue

      infos[agent_id] =  {'population': agent.population}

      rewards[agent_id] = agent.tasks.completed()
      infos[agent_id].update({agent.tasks.to_string(): agent.tasks.completed()})

    return rewards, infos


class TestTasks(unittest.TestCase):

  def test_assign_single_task_to_all(self): # without Diary and Achievement
    config = nmmo.config.Default()
    config.PLAYERS = [Sleeper]

    env = TaskWrapper(config)

    self._reset_with_task_and_run(env=env, task=Success(), ticks=10)
    self._reset_with_task_and_run(env=env, task=Failure(), ticks=10)

  def _reset_with_task_and_run(self, env, task, ticks):
    env.reset(task=task)
    for _ in range(ticks):
      _, _, _, infos = env.step({})
      task_done = env._task_completion()

      # For now, every agent is assigned the Success() task
      for eid in env.agents:
        self.assertEqual(infos[eid][task.to_string()], task.completed())
        self.assertEqual(task_done[eid], task.completed())


if __name__ == '__main__':
  unittest.main()