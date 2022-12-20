import unittest
import nmmo.lib.task as task
from nmmo.core.realm import Realm
from nmmo.entity.entity import Entity
import nmmo
import nmmo.systems.achievement as achievement
class Success(task.Task):
  def evaluate(self, realm: Realm, entity: Entity) -> bool:
    return True
  
class Failure(task.Task):
  def evaluate(self, realm: Realm, entity: Entity) -> bool:
    return False
  
class TestTask(task.CombinationTask):
  def __init__(self, target: task.VariableTarget, param1: int, param2: float) -> None:
    super().__init__(self,target,param1,param2)
    self._task = task.GEQ(task.InflictDamage(target,param1),param2)
    self._param1 = param1
    self._param2 = param2

  def evaluate(self, realm: Realm, entity: Entity) -> bool:
    return False

class MockRealm(Realm):
  def __init__(self):
    pass

class MockEntity(Entity):
  def __init__(self):
    pass

realm = MockRealm()
entity = MockEntity()

class TestTasks(unittest.TestCase):

    def test_operators(self):
      self.assertFalse(task.AND(Success(), Failure(), Success()).evaluate(realm, entity))
      self.assertTrue(task.OR(Success(), Failure(), Success()).evaluate(realm, entity))
      self.assertTrue(task.AND(Success(), task.NOT(Failure()), Success()).evaluate(realm, entity))

    def test_descriptions(self):
      self.assertEqual(
        task.AND(Success(), 
        task.NOT(task.OR(Success(), 
                         TestTask(task.VariableTarget("t1", []), 123, 3.45)))).description(),
        ['AND', 'Success', ['NOT', ['OR', 'Success', ['TestTask', 't1', '123', '3.45']]]]
      )

    def test_team_helper(self):
      team_helper = task.TeamHelper(range(1, 101), 5)
 
      self.assertSequenceEqual(team_helper.own_team(17).agents(), range(1, 21))
      self.assertSequenceEqual(team_helper.own_team(84).agents(), range(81, 101))

      self.assertSequenceEqual(team_helper.left_team(84).agents(), range(61, 81))
      self.assertSequenceEqual(team_helper.right_team(84).agents(), range(1, 21))

      self.assertSequenceEqual(team_helper.left_team(17).agents(), range(81, 101))
      self.assertSequenceEqual(team_helper.right_team(17).agents(), range(21, 41))

      self.assertSequenceEqual(team_helper.all().agents(), range(1, 101))

    def test_task_target(self):
      tt = task.VariableTarget("Foo", [1, 2, 8, 9])

      self.assertEqual(tt.member(2).description(), "Foo.2")
      self.assertEqual(tt.member(2).agents(), [8])

    def test_sample(self):
      sampler = task.TaskSampler()

      sampler.add_task_spec(Success)
      sampler.add_task_spec(Failure)
      sampler.add_task_spec(TestTask, [
        [task.VariableTarget("t1", []), task.VariableTarget("t2", [])],
        [1, 5, 10],
        [0.1, 0.2, 0.3, 0.4]
      ])

      sampler.sample(max_clauses=5, max_clause_size=5, not_p=0.5)

    def test_default_sampler(self):
      team_helper = task.TeamHelper(range(1, 101), 5)
      sampler = task.TaskSampler.create_default_task_sampler(team_helper, 10)

      sampler.sample(max_clauses=5, max_clause_size=5, not_p=0.5)

    def test_evaluate_tasks_in_info(self):
      env = nmmo.Env()
      env.config.TASKS = [
        achievement.Achievement(Success(), 10),
        achievement.Achievement(Failure(), 100)
      ]

      env.reset()
      obs, rewards, dones, infos = env.step({})

if __name__ == '__main__':
    unittest.main()