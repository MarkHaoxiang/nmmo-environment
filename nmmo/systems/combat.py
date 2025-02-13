#Various utilities for managing combat, including hit/damage
# pylint: disable=all

import numpy as np

from nmmo.systems import skill as Skill

def level(skills):
    return max(e.level.val for e in skills.skills)

def damage_multiplier(config, skill, targ):
    skills = [targ.skills.melee, targ.skills.range, targ.skills.mage]
    exp    = [s.exp for s in skills]

    if max(exp) == min(exp):
        return 1.0

    idx    = np.argmax([exp])
    targ   = skills[idx]

    if type(skill) == targ.weakness:
        return config.COMBAT_WEAKNESS_MULTIPLIER

    return 1.0

def attack(realm, player, target, skillFn):
    config       = player.config
    skill        = skillFn(player)
    skill_type   = type(skill)
    skill_name   = skill_type.__name__

    # Ammunition usage
    if config.EQUIPMENT_SYSTEM_ENABLED:
        ammunition = player.equipment.ammunition.item
        if ammunition is not None:
            ammunition.fire(player)

    # Per-style offense/defense
    level_damage = 0
    if skill_type == Skill.Melee:
        base_damage  = config.COMBAT_MELEE_DAMAGE

        if config.PROGRESSION_SYSTEM_ENABLED:
            base_damage  = config.PROGRESSION_MELEE_BASE_DAMAGE
            level_damage = config.PROGRESSION_MELEE_LEVEL_DAMAGE

        offense_fn   = lambda e: e.melee_attack
        defense_fn   = lambda e: e.melee_defense
    elif skill_type == Skill.Range:
        base_damage  = config.COMBAT_RANGE_DAMAGE

        if config.PROGRESSION_SYSTEM_ENABLED:
            base_damage  = config.PROGRESSION_RANGE_BASE_DAMAGE
            level_damage = config.PROGRESSION_RANGE_LEVEL_DAMAGE

        offense_fn   = lambda e: e.range_attack
        defense_fn   = lambda e: e.range_defense
    elif skill_type == Skill.Mage:
        base_damage  = config.COMBAT_MAGE_DAMAGE

        if config.PROGRESSION_SYSTEM_ENABLED:
            base_damage  = config.PROGRESSION_MAGE_BASE_DAMAGE
            level_damage = config.PROGRESSION_MAGE_LEVEL_DAMAGE

        offense_fn   = lambda e: e.mage_attack
        defense_fn   = lambda e: e.mage_defense
    elif __debug__:
        assert False, 'Attack skill must be Melee, Range, or Mage'

    # Compute modifiers
    multiplier        = damage_multiplier(config, skill, target)
    skill_offense     = base_damage + level_damage * skill.level.val

    if config.PROGRESSION_SYSTEM_ENABLED:
        skill_defense     = config.PROGRESSION_BASE_DEFENSE  + \
            config.PROGRESSION_LEVEL_DEFENSE*level(target.skills)
    else:
        skill_defense     = 0

    if config.EQUIPMENT_SYSTEM_ENABLED:
        equipment_offense = player.equipment.total(offense_fn)
        equipment_defense = target.equipment.total(defense_fn)
    else:
        equipment_offense = 0
        equipment_defense = 0

    # Total damage calculation
    offense = skill_offense + equipment_offense
    defense = skill_defense + equipment_defense
    damage  = config.COMBAT_DAMAGE_FORMULA(offense, defense, multiplier)
    #damage  = multiplier * (offense - defense)
    damage  = max(int(damage), 0)

    if player.is_player:
        realm.log_milestone(f'Damage_{skill_name}', damage,
                            f'COMBAT: Inflicted {damage} {skill_name} damage ' +
                            f'(lvl {player.equipment.total(lambda e: e.level)} vs' +
                            f'lvl {target.equipment.total(lambda e: e.level)})')

    player.apply_damage(damage, skill.__class__.__name__.lower())
    target.receive_damage(player, damage)

    return damage


def danger(config, pos):
   border = config.MAP_BORDER
   center = config.MAP_CENTER
   r, c   = pos

   #Distance from border
   rDist  = min(r - border, center + border - r - 1)
   cDist  = min(c - border, center + border - c - 1)
   dist   = min(rDist, cDist)
   norm   = 2 * dist / center

   return norm

def spawn(config, dnger):
    border = config.MAP_BORDER
    center = config.MAP_CENTER
    mid    = center // 2

    dist       = dnger * center / 2
    max_offset = mid - dist
    offset     = mid + border + np.random.randint(-max_offset, max_offset)

    rng = np.random.rand()
    if rng < 0.25:
        r = border + dist
        c = offset
    elif rng < 0.5:
        r = border + center - dist - 1
        c = offset
    elif rng < 0.75:
        c = border + dist
        r = offset
    else:
        c = border + center - dist - 1
        r = offset

    if __debug__:
        assert dnger == danger(config, (r,c)), 'Agent spawned at incorrect radius'

    r = int(r)
    c = int(c)

    return r, c
