import unittest
import numpy as np

import nmmo
from nmmo.core.env import TaskEnv
from nmmo.lib import task
from scripted.baselines import Sleeper, Random

# Example Task
class TravelTask(task.PredicateTask):

  def __init__(self, minimum_distance = 10):
    super().__init__()
    self.minimum_distance = minimum_distance
    self.start_position = None

  def distance_squared_to(self, new_pos) -> int:
    return (new_pos[0] - self.start_position[0])**2 + (new_pos[1] - self.start_position[1])**2

  def evaluate(self, gs: task.GameState) -> bool:
    if (self.start_position == None):
      self.start_position = gs.agent.position
    
    if self.distance_squared_to(gs.agent.position) > self.minimum_distance:
      return True
    return False

class TestTasks(unittest.TestCase):

  def _reset_with_task_and_run(self, env: TaskEnv, task: task.Task, ticks: int, map_id = 0, seed=0,) -> float:
    env.reset(task=task, map_id=map_id, seed=seed)
    total_reward = 0
    for _ in range(ticks):
      obs, rewards, dones, infos = env.step({})
      total_reward += sum(rewards.values())
    return total_reward

  def test_task_reset(self):
    TICKS = 10
    config = nmmo.config.Default()
    config.PLAYERS = [Sleeper,Sleeper]

    env = TaskEnv(config)

    r0 = self._reset_with_task_and_run(env=env, task=task.TRUE(), ticks=TICKS)
    r1 = self._reset_with_task_and_run(env=env, task=task.FALSE(), ticks=TICKS) 
    self.assertEqual(r0,config.PLAYER_N)
    self.assertEqual(r1,0)
  
  def test_travel_task(self):
    TICKS = 50
    config = nmmo.config.Default()
    config.PLAYERS = [Random, Random]

    env = TaskEnv(config)

    r0 = self._reset_with_task_and_run(env=env, task=TravelTask(minimum_distance=1), ticks=TICKS)
    r1 = self._reset_with_task_and_run(env=env, task=TravelTask(minimum_distance=2501), ticks=TICKS)
    self.assertGreater(r0,0)
    self.assertEqual(r1,0)

if __name__ == '__main__':
  unittest.main()