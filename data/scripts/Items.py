from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Engine_reference
from ugdk.ugdk_drawable import TexturedRectangle
from ugdk.ugdk_graphic import Drawable, Node
from ugdk.pyramidworks_collision import CollisionObject, CollisionLogic
from ugdk.pyramidworks_geometry import Circle
from BasicEntity import BasicEntity, EntityInterface, Group, BasicColLogic, getCollisionManager, AddNewObjectToScene
import Config
import Shockwave
import Animations
import Ship
import Weapons

from random import random, randint, shuffle
from math import pi

#########################################
class PowerUp (BasicEntity):
    def __init__(self, x, y, texture_name, lifetime, effect, name):
        r = 15.0
        BasicEntity.__init__(self, x, y, texture_name, r, 1)
        self.life_hud.node.set_active(False)
        self.max_velocity = 135.0

        self.lifespan = lifetime
        self.lifetime = lifetime
        self.effect = effect
        self.wasApplied = False
        self.blink_time = 0.0

        self.text = Engine_reference().text_manager().GetText(name)
        self.textNode = Node(self.text)
        self.textNode.modifier().set_offset( Vector2D(-self.text.width()/2.0, 0.0 ) ) # TODO: text hotspot!
        self.textNode.set_active(False)
        self.node.AddChild(self.textNode)

    def setupCollisionObject(self):
        self.collision_object = CollisionObject(getCollisionManager(), self)  #initialize collision object, second arg is passed to collisionlogic to handle collisions
        self.collision_object.InitializeCollisionClass("PowerUp")              # define the collision class
        self.geometry = Circle(self.radius)                           #
        self.collision_object.set_shape(self.geometry)                # set our shape
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        self.collision_object.thisown = 0

    def Update(self, dt):
        if not self.wasApplied:
            BasicEntity.Update(self, dt)
        self.lifetime -= dt
        if self.lifetime < self.lifespan*0.15 and not self.wasApplied:
            self.blink_time += dt
            if self.blink_time > self.lifetime/self.lifespan:
                self.blink_time = 0.0
                self.node.set_active( not self.node.active() )
        if self.lifetime < 0:
            self.Delete()

    def HandleCollision(self, target):
        if target.CheckType("Ship") and not self.wasApplied:
            self.effect.SetTarget(target)
            target.ApplyEffect(self.effect)
            self.wasApplied = True
            self.lifetime = 3.0
            self.textNode.set_active(True)
            color = self.node.modifier().color()
            color.set_a(0.2)
            self.node.modifier().set_color(color)
            self.node.set_active(True)
            #TODO: play powerup sound !

###########################
class Effect (EntityInterface):
    def __init__(self, lifetime):
        EntityInterface.__init__(self, 0, 0, 1.0)
        self.is_collidable = False
        self.target = None
        self.lifetime = lifetime
        self.unique_in_target = False #if True, there can be only 1 effect of this type in a entity simultaneously

    def Update(self, dt):
        if not self.is_destroyed and self.target != None and not self.target.is_destroyed:
            self.Apply(dt)
        self.lifetime -= dt
        if self.lifetime < 0 or (self.target != None and self.target.is_destroyed):
            self.Delete()

    def SetTarget(self, target):
        self.target = target

    def Apply(self, dt):
        pass

#############
class AbsoluteLifeEffect (Effect):
    def __init__(self, lifetime, amount, doHeal=True, isRegen=False):
        Effect.__init__(self, lifetime)
        self.amount = amount
        self.heals = doHeal
        self.regen = isRegen

    def Apply(self, dt):
        value = self.amount
        if self.regen:
            value *= dt
        if not self.heals:
            self.target.TakeDamage(value)
        else:
            self.target.Heal(value)
################
class AbsoluteEnergyEffect (Effect):
    def __init__(self, lifetime, amount, isRegen=False):
        Effect.__init__(self, lifetime)
        self.amount = amount
        self.regen = isRegen

    def Apply(self, dt):
        value = self.amount
        if self.regen:
            value *= dt
        self.target.RestoreEnergy(value)
#################
class MaxValueIncreaseEffect (Effect):
    ENERGY = "energy"
    LIFE = "life"
    def __init__(self, valueTypeName, amount):
        Effect.__init__(self, 0)
        self.amount = amount
        self.valueTypeName = valueTypeName

    def Apply(self, dt):
        if self.valueTypeName == MaxValueIncreaseEffect.ENERGY:
            self.target.set_max_energy( self.target.max_energy + self.amount )
            self.target.energy += self.amount
        elif self.valueTypeName == MaxValueIncreaseEffect.LIFE:
            self.target.set_max_life( self.target.max_life + self.amount )
            self.target.life += self.amount

##################
class PulseDamageIncreaseEffect(Effect):
    def __init__(self, amount):
        Effect.__init__(self, 0)
        self.amount = amount
    def Apply(self, dt):
        self.target.data.pulse_damage += self.amount

##################
class PulseMultiplicityIncreaseEffect(Effect):
    def __init__(self, amount):
        Effect.__init__(self, 0)
        self.amount = amount
    def Apply(self, dt):
        self.target.data.pulse_shots += self.amount

##################
class PulseHomingEffect(Effect):
    def __init__(self, amount):
        Effect.__init__(self, 0)
        self.amount = amount
    def Apply(self, dt):
        if self.target.data.homing >= 1.0:  self.target.data.homing = 1.0
        else: self.target.data.homing += self.amount

#################
class SatelliteEffect(Effect):
    def __init__(self):
        Effect.__init__(self, 10)
        self.sat1 = None
        self.sat2 = None
        self.unique_in_target = True

    def OnSceneAdd(self, scene):
        self.sat1 = Ship.Satellite(self.target, 100, pi/2.0)
        self.sat2 = Ship.Satellite(self.target, 100, 3*pi/2.0)
        AddNewObjectToScene(self.sat1)
        AddNewObjectToScene(self.sat2)

    def Apply(self, dt):
        if (self.sat1.is_destroyed and self.sat2.is_destroyed) or self.target.is_destroyed:
            self.sat1.Delete()
            self.sat2.Delete()
            self.lifetime = 0.0
        else:
            self.lifetime = 10.0

    def Update(self, dt):
        Effect.Update(self,dt)
        if self.is_destroyed:
            self.sat1.Delete()
            self.sat2.Delete()

    def Delete(self):
        Effect.Delete(self)
        if not self.sat1.is_destroyed: self.sat1.Delete()
        if not self.sat2.is_destroyed: self.sat2.Delete()

#################
class ShieldEffect(Effect):
    def __init__(self, life):
        Effect.__init__(self, 10)
        self.max_life = life
        self.life = life
        self.is_collidable = True
        self.unique_in_target = True
        self.collision_object = CollisionObject(getCollisionManager(), self)
        self.collision_object.InitializeCollisionClass("PowerUp")
        self.geometry = Circle(1.0)
        self.geometry.thisown = 0
        self.collision_object.set_shape( self.geometry )

    def OnSceneAdd(self, scene):
        self.radius = self.target.radius * 1.2
        self.size = Vector2D(self.radius*2, self.radius*2)
        texture_name = "images/shockwave.png"
        texture_obj = Engine_reference().resource_manager().texture_container().Load(texture_name, texture_name)

        self.shape = TexturedRectangle( texture_obj, self.size )
        self.shape.set_hotspot(Drawable.CENTER)
        self.node.set_drawable(self.shape)
        color = self.node.modifier().color()
        color.set_a(0.5)
        self.node.modifier().set_color(color)

        self.geometry = Circle(self.radius)
        self.collision_object.set_shape(self.geometry)
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        

    def Apply(self, dt):
        self.SetPos( self.target.GetPos() )
        if self.life > 0 and not self.target.is_destroyed:
            self.lifetime = 10.0
        else:
            self.lifetime = 0.0

    def HandleCollision(self, coltarget):
        if coltarget.CheckType("Asteroid") or (coltarget.CheckType("Projectile") and coltarget.GetParentID() != self.target.id):
            self.life -= coltarget.GetDamage(self.target.type)
            coltarget.TakeDamage(coltarget.life + 10)
            #print "SHIELD COLLISION %s/%s" % (self.life, self.max_life)

#####################
class ItemAttractorEffect(Effect):
    def __init__(self, lifetime, radius, force):
        Effect.__init__(self, lifetime)
        self.radius = radius
        self.is_collidable = True
        self.unique_in_target = True
        self.force = force
        self.collision_object = CollisionObject(getCollisionManager(), self)
        self.collision_object.InitializeCollisionClass("PowerUp")
        self.geometry = Circle(self.radius)
        self.collision_object.set_shape(self.geometry)
        self.collision_object.AddCollisionLogic("PowerUp", BasicColLogic(self) )
        
    def Apply(self, dt):
        self.SetPos( self.target.GetPos() )

    def HandleCollision(self, coltarget):
        if coltarget.CheckType("PowerUp"): # we can collide with any powerup or collidable effect, however we only affect powerups (the actual item)...
            v = self.GetPos() - coltarget.GetPos()
            v = v.Normalize()
            v = v * self.force
            coltarget.ApplyVelocity(v)

####################
class MatterAbsorptionEffect(Effect):
    def __init__(self, duration, life_absorbed_percent, energy_absorbed_percent):
        Effect.__init__(self, duration)
        self.life_absorbed_percent = life_absorbed_percent
        self.energy_absorbed_percent = energy_absorbed_percent
        self.is_collidable = True
        self.unique_in_target = True
        self.collision_object = CollisionObject(getCollisionManager(), self)
        self.collision_object.InitializeCollisionClass("PowerUp")
        self.geometry = Circle(1.0)
        self.geometry.thisown = 0
        self.collision_object.set_shape( self.geometry )

    def OnSceneAdd(self, scene):
        self.radius = self.target.radius * 1.1
        self.size = Vector2D(self.radius*2, self.radius*2)
        texture_name = "images/shockwave.png"
        texture_obj = Engine_reference().resource_manager().texture_container().Load(texture_name, texture_name)

        self.shape = TexturedRectangle( texture_obj, self.size )
        self.shape.set_hotspot(Drawable.CENTER)
        self.node.set_drawable(self.shape)
        color = self.node.modifier().color()
        color.set_a(0.5)
        self.node.modifier().set_color(color)

        self.geometry = Circle(self.radius)
        self.collision_object.set_shape(self.geometry)
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        
    def Apply(self, dt):
        self.SetPos( self.target.GetPos() )

    def HandleCollision(self, coltarget):
        if hasattr(coltarget, "GetGroup") and coltarget.GetGroup() != self.target.GetGroup() and coltarget.GetGroup() != Group.NEUTRAL:
            if coltarget.CheckType("Asteroid"):
                self.target.Heal(coltarget.life * self.life_absorbed_percent)
            elif coltarget.CheckType("Projectile"):
                self.target.RestoreEnergy(coltarget.GetDamage(self.target.type) * self.energy_absorbed_percent)
            coltarget.TakeDamage(coltarget.life + 10)

####################
class WeaponPickupEffect(Effect):
    def __init__(self, weapon):
        Effect.__init__(self, 0)
        self.weapon = weapon
    def Apply(self, dt):
        self.target.SetRightWeapon(self.weapon)

####################
class ShockwaveEffect(Effect):
    def __init__(self, shock_lifetime, shock_radius_range, shock_damage, wave_damage):
        Effect.__init__(self, 0)
        self.shock_lifetime = shock_lifetime
        self.shock_radius_range = shock_radius_range
        self.shock_damage = shock_damage    # done once when shockwave hits a target
        self.wave_damage = wave_damage      # done continously while shockwave pushes a target

    def Apply(self, dt):
        pos = self.target.GetPos()
        wave = Shockwave.Shockwave(pos.get_x(), pos.get_y(), self.shock_lifetime, self.shock_radius_range)
        wave.shock_damage = self.shock_damage
        wave.wave_damage = self.wave_damage
        wave.shock_force_factor = 0.4
        wave.AddIDToIgnoreList(self.target.id)
        AddNewObjectToScene(wave)
        exploAnim = Animations.CreateExplosionAtLocation(pos, self.shock_radius_range[1])
        AddNewObjectToScene(exploAnim)

##################
class FractureEffect(Effect):
    def __init__(self):
        Effect.__init__(self, 0)

    def Apply(self, dt):
        scene = Engine_reference().CurrentScene()
        # It's possible that since new objects are added directly to the AsteroidsScene, the new asteroids
        # created on breaking will be place in this list, and then we'll fracture them too... Can't let that happen =P
        asteroid_list = [o for o in scene.objects if o.CheckType("Asteroid")]
        for obj in asteroid_list:
            if obj.CheckType("Asteroid"):
                exploAnim = Animations.CreateExplosionAtLocation(obj.GetPos(), obj.radius)
                AddNewObjectToScene(exploAnim)
                obj.Break()

##################
class FractalShotEffect(Effect):
    def __init__(self):
        Effect.__init__(self, 0)

    def Apply(self, dt):
        pos = self.target.GetPos()
        dir = self.target.GetDirection()
        dir = dir.Normalize()
        dir = dir * (self.target.radius*2)
        pos = pos + dir
        dir = dir.Normalize()
        dir = dir * ( self.target.velocity.Length()*1.3 )
        depth = randint(2,5)
        shot = Weapons.FractalShot(pos.get_x(), pos.get_y(), dir, depth)
        shot.SetParent(self.target)
        AddNewObjectToScene(shot)

###################
class UpdateExchangerEffect(Effect):
    def __init__(self, lifetime, new_Update):
        Effect.__init__(self, lifetime)
        self.new_Update = new_Update
        self.real_Update = None
        self.applied = False
        self.effect_attr = None
        self.unique_in_target = True

    def Apply(self, dt):
        if not self.applied:
            self.applied = True
            self.real_Update = self.target.Update
            def updateOverwrite(object, dt):
                args = [object, dt, self.real_Update, self.effect_attr]
                try:
                    self.new_Update(*args)
                except:
                    self.new_Update(object, dt)
            self.target.Update = updateOverwrite

    def Update(self, dt):
        Effect.Update(self, dt)
        if self.is_destroyed and self.applied:
            self.target.Update = self.real_Update

    def Delete(self):
        if self.applied:
            self.target.Update = self.real_Update
        Effect.Delete(self)
        

#################
class FreezeEffect(Effect):
    def __init__(self, freeze_time):
        Effect.__init__(self, 0)
        self.freeze_time = freeze_time

    def Apply(self, dt):
        scene = Engine_reference().CurrentScene()
        for obj in scene.objects:
            if hasattr(obj, "GetGroup") and obj.GetGroup() != self.target.GetGroup() and obj.GetGroup() != Group.NEUTRAL:
                e = UpdateExchangerEffect(self.freeze_time, FreezeEffect.FreezeUpdate)
                e.SetTarget(obj)
                obj.ApplyEffect(e)

    @staticmethod
    def FreezeUpdate(self, dt):
        if hasattr(self, "life_hud"):
            self.life_hud.Update()
        elif hasattr(self, "energy_hud"):
            self.energy_hud.Update()

#################
class SlowdownEffect(Effect):
    def __init__(self, slowdown_time, slowdown_percent):
        Effect.__init__(self, 0)
        self.slowdown_time = slowdown_time
        self.slowdown_percent = slowdown_percent

    def Apply(self, dt):
        scene = Engine_reference().CurrentScene()
        for obj in scene.objects:
            if hasattr(obj, "GetGroup") and obj.GetGroup() != self.target.GetGroup() and obj.GetGroup() != Group.NEUTRAL:
                e = UpdateExchangerEffect(self.slowdown_time, SlowdownEffect.SlowdownUpdate)
                e.effect_attr = self.slowdown_percent
                e.SetTarget(obj)
                obj.ApplyEffect(e)

    @staticmethod
    def SlowdownUpdate(self, dt, real_Update, effect_attr):
        actual_dt = dt * effect_attr
        real_Update(actual_dt)