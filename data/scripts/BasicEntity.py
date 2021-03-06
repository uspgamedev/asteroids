from ugdk.ugdk_graphic import Node, Modifier, Drawable
from ugdk.ugdk_drawable import TexturedRectangle
from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Color, Engine_reference
from ugdk.ugdk_action import Entity
from ugdk.pyramidworks_collision import CollisionObject, CollisionLogic
from ugdk.pyramidworks_geometry import Circle
from Radio import SOUND_PATH
from BarUI import BarUI
from random import randint
import Config

MANAGER = None

def getCollisionManager():
    scene = Engine_reference().CurrentScene()
    #print "Getting COLLISION MANAGER from ", scene
    return scene.collisionManager

def AddNewObjectToScene(obj):
    scene = Engine_reference().CurrentScene()
    scene.AddObject(obj)

class EntityInterface (Entity):
    nextID = 1
    def __init__(self, x, y, radius):
        self.radius = radius
        self.is_destroyed = False
        self.to_be_removed = False
        self.is_collidable = True
        self.collision_object = None

        self.hud_node = Node()
        self.node = Node()
        self.SetPos( Vector2D(x,y) )

        # Calculating Type
        self.type = str(self.__class__)
        if len(self.type.split("'")) > 1:
            self.type = self.type.split("'")[1]
        self.type = self.type.split(".")[1]

        # Get Unique ID
        self.id = EntityInterface.nextID
        EntityInterface.nextID += 1

    def CheckType(self, typestr):
        return self.type.count(typestr) > 0

    def ClearNewObjects(self):
        self.new_objects = []

    def GetNode(self):  return self.node
    def GetHUDNode(self):   return self.hud_node

    def GetPos(self):
        return self.node.modifier().offset()

    def SetPos(self, pos):
        self.node.modifier().set_offset(pos)
        self.hud_node.modifier().set_offset(pos)
        if self.collision_object != None:
            self.collision_object.MoveTo(pos)

    def GetDirection(self):
        return Vector2D(0.0, 1.0)

    def GetPointsValue(self):
        return 0

    def HandleMapBoundaries(self, pos):
        max = Config.gamesize

        passedBoundary = False
        # checking for horizontal map boundaries
        if pos.get_x() < 0.0:
            pos.set_x( max.get_x() + pos.get_x() )
            passedBoundary = True
        if pos.get_x() > max.get_x():
            pos.set_x( pos.get_x() - max.get_x() )
            passedBoundary = True

        # checking for vertical map boundaries
        if pos.get_y() < 0.0:
            pos.set_y( max.get_y() + pos.get_y() )
            passedBoundary = True
        if pos.get_y() > max.get_y():
            pos.set_y( pos.get_y() - max.get_y() )
            passedBoundary = True
        return passedBoundary
            
    def Update(self, dt):
        pass

    def HandleCollision(self, target):
        print self.type, " HandleCollision NOT IMPLEMENTED"
        
    def Delete(self):
        if hasattr(self, "node") and self.node != None:
            self.node.set_active(False)
        if self.is_destroyed:   return
        self.is_destroyed = True        

    def __repr__(self):
        return "<%s #%s>" % (self.type, self.id)
        
    def __str__(self): return self.__repr__()
    
    
class BasicColLogic(CollisionLogic):
    def __init__(self, entity):
        self.entity = entity
    def Handle(self, data):
        self.entity.HandleCollision(data)

 
class Group:
    UNDETERMINED = -1  #when undetermined, check parent's group, or return neutral
    NEUTRAL = 0
    SHIP = 1
    ASTEROIDS = 2

class BasicEntity (EntityInterface):
    nextID = 1
    def __init__(self, x, y, texture_name, radius, life, WtoHratio=1.0):
        EntityInterface.__init__(self, x, y, radius)
        self.size = Vector2D(self.radius*2, self.radius*2*WtoHratio)
        texture_obj = Engine_reference().resource_manager().texture_container().Load(texture_name, texture_name)

        self.shape = TexturedRectangle( texture_obj, self.size )
        self.shape.set_hotspot(Drawable.CENTER)
        self.node.set_drawable(self.shape)

        #self.text = Engine_reference().text_manager().GetText( "#"+str(self.id) )
        #self.text.set_hotspot(Drawable.CENTER)
        #self.textNode = Node(self.text)
        #self.textNode.modifier().set_offset( Vector2D(0.0, -self.radius ) )
        #self.hud_node.AddChild(self.textNode)

        self.velocity = Vector2D(0.0, 0.0)
        self.max_velocity = 5000.0 #length of the maximum velocity - the entity can't achieve a velocity with length greater than this by whatever means
        self.last_velocity = None
        self.last_dt = 0.000001
        self.life = life
        self.max_life = life
        self.hit_sounds = ["hit1.wav", "hit2.wav", "hit3.wav", "hit4.wav"]
        self.life_hud = BarUI(self, "life", Color(1.0,0.0,0.0,1.0), self.radius)
        self.hud_node.AddChild(self.life_hud.node)
        self.active_effects = {}
        self.group = Group.UNDETERMINED
        self.wraps_around_boundary = True
        self.invulnerable = False
        self.setupCollisionGeometry()
        self.setupCollisionObject()

    def setupCollisionGeometry(self):
        self.geometry = Circle(self.radius)

    def setupCollisionObject(self):
        self.collision_object = CollisionObject(getCollisionManager(), self)  #initialize collision object, second arg is passed to collisionlogic to handle collisions
        self.collision_object.InitializeCollisionClass("Entity")              # define the collision class
        self.collision_object.set_shape(self.geometry)                # set our shape
        #finally add collision logics to whatever collision class we want
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        self.collision_object.thisown = 0

    def ApplyEffect(self, effect):
        #since effects are entities too, we just do this
        AddNewObjectToScene(effect)
        if self.active_effects.has_key(effect.type):
            if effect.unique_in_target:
                for e in self.active_effects[effect.type]:
                    e.Delete()
            self.active_effects[effect.type].append(effect)
        else:
            self.active_effects[effect.type] = [effect]

    def GetActiveEffectsDetailsList(self):
        aedl = []
        for effectType, effects in self.active_effects.items():
            countStr = ""
            count = len(effects)
            if count <= 0:  continue
            if count > 1:
                countStr = "%sx " % count
            if effects[0].GetDetailString() != "":
                aedl.append( countStr+effects[0].GetDetailString() )
        return aedl

    def GetActiveEffectsList(self):
        el = []
        for effectType, effects in self.active_effects.items():
            el = el + effects
        return el
        
    def CleanUpActiveEffects(self):
        for effectType, effects in self.active_effects.items():
            for e in effects:
                if e.is_destroyed:
                    self.active_effects[effectType].remove(e)

    def GetGroup(self):
        if self.group == Group.UNDETERMINED:
            if hasattr(self, "parent"):
                return self.parent.GetGroup()
            return Group.NEUTRAL
        return self.group

    def Update(self, dt): ###
        self.UpdatePosition(dt)
        self.CleanUpActiveEffects()
        self.life_hud.Update()
        if self.velocity.Length() > self.max_velocity:
            self.velocity = self.velocity * (self.max_velocity / self.velocity.Length())

    def UpdatePosition(self, dt):
        pos = self.GetPos()
        pos = pos + (self.velocity * dt)
        self.last_velocity = self.velocity
        self.last_dt = dt
        if self.HandleMapBoundaries(pos) and not self.wraps_around_boundary:
            self.Delete()
        self.SetPos(pos)

    def GetDirection(self):
        if self.velocity.Length() == 0.0:
            return Vector2D(0.0, 1.0)
        return self.velocity.Normalize()

    def GetDamage(self, obj_type):
        # returns the amount of damage this object causes on collision with given obj_type
        print self.type, " GetDamage NOT IMPLEMENTED"

    def TakeDamage(self, damage):
        if damage < 0:  return
        if self.invulnerable:   return
        self.life -= damage
        if damage > 0:
            sound_name = self.hit_sounds[ randint(0, len(self.hit_sounds)-1) ]
            sound = Engine_reference().audio_manager().LoadSample(SOUND_PATH + sound_name)
            sound.Play()
        if self.life <= 0:
            self.Delete()
        #print self, "took %s damage, current life = %s [max life =%s]" % (damage, self.life, self.max_life)

    def Heal(self, amount):
        if amount < 0:  return
        self.life += amount
        if self.life > self.max_life:
            self.life = self.max_life
        #print self, "has recovered %s life, current life = %s" % (amount, self.life)
        
    def ApplyVelocity(self, v):
        self.velocity = self.velocity + v

    def ApplyCollisionRollback(self):
        if self.is_destroyed:   return
        pos = self.GetPos()
        v = self.last_velocity
        if not v:   v = self.velocity
        pos = pos + (v * -self.last_dt)
        self.HandleMapBoundaries(pos)
        pos = pos + (self.velocity * self.last_dt)
        self.HandleMapBoundaries(pos)
        self.SetPos(pos)
        self.last_velocity = self.velocity
    
####################
class RangeCheck(EntityInterface):
    def __init__(self, x, y, radius, target_type):
        EntityInterface.__init__(self, x, y, radius)
        self.parent = None
        self.target_type = target_type
        self.target = None
        self.dist = -1.0
        self.setupCollisionObject()

    def setupCollisionObject(self):
        self.collision_object = CollisionObject(getCollisionManager(), self)  #initialize collision object, second arg is passed to collisionlogic to handle collisions
        self.collision_object.InitializeCollisionClass("RangeCheck")              # define the collision class
        self.geometry = Circle(self.radius)                           #
        self.collision_object.set_shape(self.geometry)                # set our shape
        #finally add collision logics to whatever collision class we want
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        self.collision_object.thisown = 0

    def GetTarget(self):
        return self.target

    def SetRadius(self, r):
        self.radius = r
        self.geometry.set_radius(r)
    
    def AttachToEntity(self, ent):
        self.parent = ent
        AddNewObjectToScene(self)

    def Update(self, dt):
        if self.parent != None:
            if self.parent.is_destroyed:
                self.Delete()
            else:
                self.SetPos(self.parent.GetPos())
        if self.target != None:
            if self.target.is_destroyed:
                self.target = None
                self.dist = -1.0
            else:
                self.dist = self.GetDistTo(self.target)

    def GetDistTo(self, ent):
        d = self.GetPos() - ent.GetPos()
        return d.Length()

    def HandleCollision(self, coltarget):
        if coltarget.CheckType(self.target_type):
            d = self.GetDistTo(coltarget)
            #if self.target_type == "Asteroid" and d < 150:
            #    print "[%s :: %s] => [%s :: %s]" % (self.target,self.dist,  coltarget,d)
            if self.target == None or d < self.dist:
                self.target = coltarget
                self.dist = d

#################################################
# utility functions
#################################################

# GetEquivalentValueInRange()
###
# given origin_value, which should be a value in the range origin_range ( [origin_range[0], origin_range[1]] )
# and the destination_range, this function returns the equivalent value of origin_value in the destination_range,
# based on the ranges.
###
# if origin_value = X, origin_range = [A, B], destination_range = [C, D], then this function returns V so that:
# (V-C)/(D-C) = (X-A)/(B-A)
#   <=>
# V = C + (D-C)(X-A)/(B-A)
def GetEquivalentValueInRange(origin_value, origin_range, destination_range):
    xa = origin_value - origin_range[0]                 # xa = X - A
    ba = origin_range[1] - origin_range[0]              # ba = B - A
    if ba == 0.0:  #Go POG! Go POG!
        ba = 0.0001
    dc = destination_range[1] - destination_range[0]    # dc = D - C
    r = dc * xa / ba                                    # r = (D-C)(X-A)/(B-A)
    return destination_range[0] + r       # return C + r


#### momentum
# MaVa + MbVb = MaVa' + MbVb'
# 1 = e = (Vb' - Va')/(Va-Vb)
###
# following momentum formulas, returns a pair of the speeds (velocity magnetude) of each entity (in order) after a collision
def CalculateAfterSpeedBasedOnMomentum(v1, m1, v2, m2, e=0.2):
    #nv1 = ((2*m2*v2) + (v1 * (m1 - m2))) / (m1 + m2)
    #nv2 = ((2*m1*v1) + (v2 * (m2 - m1))) / (m2 + m1)
    nv1 = ( m2*e*(v2-v1) + (m1*v1) + (m2*v2) ) / (m1 + m2)
    nv2 = ( m1*e*(v1-v2) + (m1*v1) + (m2*v2) ) / (m1 + m2)
    return (nv1, nv2)

#####
# SeparateVectorComponents
###
# separates the given vector v into its components A and B
# where A is the component in the line represented by dir
# and B is the component in the line perpendicular to dir
# return (A, B)
def SeparateVectorComponents(v, dir):
    dirPerpendicular = Vector2D( -dir.get_y(), dir.get_x() )
    v1 = dir * (dir * v)
    v2 = dirPerpendicular * (dirPerpendicular * v)
    return (v1, v2)

