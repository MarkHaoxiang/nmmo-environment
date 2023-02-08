import unittest

from nmmo.lib.task import  GameStateGenerator, Task, TRUE, FALSE, AND, OR
import nmmo
from scripted.baselines import Sleeper


class TestTaskDefinitions(unittest.TestCase):

    def test_predicate_combination_task(self):
        self.assertTrue((FALSE() >> TRUE()).evaluate(None))
        self.assertTrue((FALSE() | TRUE()).evaluate(None))
        self.assertFalse((AND(TRUE(),TRUE(),FALSE(),TRUE())).evaluate(None))
        self.assertTrue(OR(TRUE(),TRUE(),FALSE(),TRUE()).evaluate(None))
        self.assertRaises(AttributeError,OR(Task(),TRUE()).evaluate,None)

    def test_create_gs(self):
        config = nmmo.config.Default()
        config.PLAYERS = [Sleeper, Sleeper]
        env = nmmo.Env(config)
        env.reset()

        generator = GameStateGenerator(env.realm,config)
        game_state = generator.generate([v for v in env.realm.players.values()][0].ent_id)
        
        self.assertEqual(game_state.agent.health,config.PLAYER_BASE_HEALTH)
        self.assertNotEqual(game_state.team[0].position, game_state.opponents[1][0].position)

if __name__ == '__main__':
  unittest.main()