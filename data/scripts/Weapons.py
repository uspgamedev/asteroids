from ugdk.ugdk_math import Vector2D, Vector2DList
from ugdk.ugdk_base import Engine_reference, Color
from ugdk.ugdk_graphic import Node, Drawable
from BasicEntity import EntityInterface, BasicEntity, Group, RangeCheck, AddNewObjectToScene, GetEquivalentValueInRange, getCollisionManager, BasicColLogic
from Animations import CreateExplosionFromCollision, CreateExplosionAtLocation
from Radio import SOUND_PATH
import Shockwave
import Gravity

from random import random, randint
from math import pi, ceil, acos


def PlaySound(sound_name):
    sound = Engine_reference().audio_manager().LoadSample(SOUND_PATH + sound_name)
    sound.Play()


class Projectile (BasicEntity):
    base_radius = 5.0
    @staticmethod
    def GetActualRadius(power):
        return Projectile.base_radius * power

    def __init__(self, x, y, velocity, power, damage = 25.0, isFromPlayer=False):
        self.parent = None #game entity that "owns" this projectile
        self.power = power
        self.damage = damage * power
        self.original_damage = self.damage
        self.lifetime = 10.0 * power
        self.original_radius = Projectile.GetActualRadius(power)
        BasicEntity.__init__(self, x, y, "images/projectile.png", self.original_radius, self.damage)
        self.shape.set_hotspot( Vector2D(32.0, 32.0) )
        self.shape.set_size( Vector2D(64, 128) )  # original projectile.png size
        self.on_hit_events = []
        #self.tracking_target = None
        self.tracking_coefficient = 0.0

        self.rangeCheck = None

        self.isFromPlayer = isFromPlayer
        self.hitsFriendlyToParent = True
        self.hitsSameClassAsParent = True
        # scale:
        # base_radius <=> 0.5 (scale value)
        # 
        # radius <=> scale
        scale = self.radius * 0.20 / Projectile.base_radius
        self.node.modifier().set_scale( Vector2D(scale, scale) )
        self.node.modifier().set_rotation( -(velocity.Angle() + pi/2.0) )
        self.velocity = velocity
        self.value = 0
        self.life_hud.node.set_active(False)

    def Update(self, dt):
        self.UpdatePosition(dt)
        if self.tracking_target != None and self.tracking_coefficient > 0.0:
            if self.tracking_target.is_destroyed:
                self.tracking_target = None
            else:
                dir = (self.tracking_target.GetPos() - self.GetPos()).Normalize()# * speed
                angle = dir.Angle() - self.velocity.Angle()
                if angle < -pi: angle += 2*pi
                elif angle > pi:    angle -= 2*pi
                rotangle = (0.5+self.tracking_coefficient)*pi/3
                if angle < 0:   rotangle = -rotangle
                self.velocity = self.velocity.Rotate( rotangle * dt )
        self.node.modifier().set_rotation( -(self.velocity.Angle()+pi/2.0) )
        self.lifetime -= dt
        if self.lifetime <= 0:
            #gotta destroy this thing
            self.CallOnHitEvents(None)
            self.Delete()

    def SetParent(self, parent):
        self.parent = parent

    def GetParentID(self):
        if self.parent != None:
            return self.parent.id
        return -1

    def TakeDamage(self, damage):
        BasicEntity.TakeDamage(self, damage)
        if not self.is_destroyed:
            self.radius = self.original_radius * self.life / self.original_damage
            scale = self.radius * 0.20 / Projectile.base_radius
            self.damage = self.life
            self.node.modifier().set_scale( Vector2D(scale, scale) )

    def GetDamage(self, obj_type):
        if obj_type == "Planet":
            return self.damage * 0.05
        return self.damage

    def GetPointsValue(self):
        return self.value

    @property
    def tracking_target(self):
        if self.rangeCheck != None:
            return self.rangeCheck.GetTarget()
        return None

    def SetTrackingTarget(self, trackingTarget, trackingCoefficient):
        #self.tracking_target = trackingTarget
        self.tracking_coefficient = trackingCoefficient
        self.rangeCheck = RangeCheck(0, 0, 200.0, "Asteroid")
        self.rangeCheck.AttachToEntity(self)

    def AddOnHitEvent(self, function):
        self.on_hit_events.append(function)

    def CallOnHitEvents(self, target):
        for f in self.on_hit_events:
            f(self, target)

    def IsParentFriendlyToEntity(self, ent):
        if self.parent == None: return False

        return self.GetGroup() == ent.GetGroup()

    def HandleCollision(self, target):
        if self.isFromPlayer and target.CheckType("Asteroid"):
            self.value = self.life / 2

        if not self.hitsFriendlyToParent and self.IsParentFriendlyToEntity(target):
            return
        if not self.hitsSameClassAsParent and target.type == self.parent.type:
            return

        if target.CheckType("Projectile"):
            # collision between projectiles, destroy both
            target.TakeDamage(self.GetDamage(target.type))
            if target.is_destroyed:
                target.CallOnHitEvents(self)
            CreateExplosionFromCollision(self, target, self.radius*5)
            #print "Projectiles exploding..."
        elif target.CheckType("Ship") or target.CheckType("Asteroid"):
            target.TakeDamage(self.GetDamage(target.type))
            target.ApplyVelocity(self.velocity * (0.1*self.power))
            self.Delete()
            CreateExplosionFromCollision(self, target, target.radius)
            self.CallOnHitEvents(target)
            #print "Projectile damaging ", target.type
        elif target.CheckType("Planet"):
            target.TakeDamage(self.GetDamage(target.type))
            self.Delete()
            CreateExplosionFromCollision(self, target, target.radius*0.7)
            self.CallOnHitEvents(target)
            #print "Projectile impacted planet"
        elif target.CheckType("Satellite") and not self.isFromPlayer:
            target.TakeDamage(self.GetDamage(target.type))
            self.Delete()
            CreateExplosionFromCollision(self, target, target.radius)
            self.CallOnHitEvents(target)
            
#########################
class Turret:
    def __init__(self, parent, target_type, cooldown, speed, power, color=None):
        self.parent = parent
        self.cooldown = cooldown
        self.elapsed = 0.0
        self.speed = speed
        self.power = power
        self.color = color
        self.firing_angle_offset = 2.5 #degrees
        self.hitsFriendlyToParent = True
        self.hitsSameClassAsParent = True
        self.rangeCheck = RangeCheck(0, 0, 500.0, target_type)
        self.rangeCheck.AttachToEntity(parent)
    
    def Update(self, dt):
        self.elapsed += dt
        if self.elapsed > self.cooldown:
            self.elapsed = 0.0
            target = self.GetTarget()
            if target != None:
                self.Shoot( target )

    def GetTarget(self):
        return self.rangeCheck.GetTarget()

    def GetShootingAngle(self):
        r = random()
        r = r * (self.firing_angle_offset*2)
        return r - self.firing_angle_offset

    def Shoot(self, target):
        pos = self.parent.GetPos()
        dir = target.GetPos() - pos
        dir = dir.Normalize()
        pos = pos + (dir * 1.1 * (self.parent.radius + Projectile.GetActualRadius(self.power)) )

        target_future_pos = target.GetPos() + target.velocity
        dir = (target_future_pos - pos).Normalize()

        parent_speed_factor = self.parent.velocity.Normalize()*dir.Normalize()
        if parent_speed_factor < -0.2:  parent_speed_factor = -0.2
        vel = dir * (self.speed + parent_speed_factor*self.parent.velocity.Length())
        angle = self.GetShootingAngle() #angle is in degrees
        angle = angle * pi / 180.0
        vel = vel.Rotate( angle ) #we need angle in radians
        proj = Projectile(pos.get_x(), pos.get_y(), vel, self.power)
        proj.SetParent(self.parent)
        proj.hitsFriendlyToParent = self.hitsFriendlyToParent
        proj.hitsSameClassAsParent = self.hitsSameClassAsParent
        if self.color != None:
            proj.node.modifier().set_color( self.color )
        AddNewObjectToScene(proj)
        PlaySound("fire.wav")


###################################
class Weapon:
    def __init__(self):
        self.parent = None
        self.type = str(self.__class__)
        self.creation_func = None
        if len(self.type.split("'")) > 1:
            self.type = self.type.split("'")[1]
        self.type = self.type.split(".")[1]
    def Activate(self, parent):
        self.parent = parent
    def Toggle(self, active, dt):
        return False # return -> boolean indicating if weapon succesfully fired
    def Dismantle(self):
        pass # this function should perform any action necessary to kill/destroy/remove this weapon.
    def GetCreationFunc(self):
        return (self.creation_func, {})
    def __repr__(self):
        return "%s" % (self.type)
    def __str__(self): return self.__repr__()

########
def GetMultiShotSpreadThreshold():
    screenSize = Engine_reference().video_manager().video_size()
    l = min(screenSize.get_x(), screenSize.get_y())
    return l * 0.5

def GetMultiShotData(num_shots, entity, direction, target_distance, projectile_power, projectile_speed):
    # calculating index for all shots
    N = num_shots
    shotIndexList = range(-(N-int(ceil(N/2.0))), int(ceil(N/2.0)))
    indexOffset = 0
    if N % 2 == 0:
        indexOffset = 0.5
    #creating shots...
    ret = []
    for i in shotIndexList:
        #first calculate the initial projectile position, based in a circle centered on the parent
        pos = entity.GetPos()
        ent_firing_distance = min(entity.size.get_x(), entity.size.get_y())*0.7
        dir = direction.Normalize() * (ent_firing_distance + Projectile.GetActualRadius(projectile_power)) #centralized forward facing direction
        dir = dir.Rotate( (i+indexOffset) * (pi/7) )
        pos = pos + dir
        #then calculate direction/velocity of the projectile, based on distance of mouse to the ship (closer = spread / far = concentrated)
        velDir = direction.Normalize()
        spreadThreshold = GetMultiShotSpreadThreshold()
        if target_distance < spreadThreshold:
            velDir = velDir.Rotate( (i+indexOffset) * (pi/7) * ( (spreadThreshold-target_distance)/spreadThreshold ) )
        parent_speed_factor = velDir*entity.velocity.Normalize()
        if parent_speed_factor < -0.2:  parent_speed_factor = -0.2
        vel = velDir * (projectile_speed + parent_speed_factor*entity.velocity.Length())
        ret.append( (pos, vel) )
    return ret

########
class Pulse (Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.shot_cost = 5.0                # energy required to shoot the weakest projectile
        self.max_charge_time = 1.0          # max time that you can charge a shot in seconds
        self.charge_time = 0                # used internally for counting, in seconds
        self.power_range = [0.5, 3.0]       # range in which the shot can be
        self.projectile_speed = 250         #
        self.target = None
        self.can_shoot = True

    @property
    def size(self):
        return self.parent.size

    def SetTarget(self, target):
        self.target = target

    def Toggle(self, active, dt):
        
        if active and self.can_shoot:
            self.charge_time += dt
            if self.charge_time >= self.max_charge_time:
                self.charge_time = self.max_charge_time
        elif not active and not self.can_shoot: self.can_shoot = True

        power = self.GetPower()
        cost = self.GetEnergyCost(power)

        if active and self.can_shoot and self.parent.energy < cost:
            self.charge_time -= dt

        if (not active and self.charge_time > 0):
            mouse_dir = Engine_reference().input_manager().GetMousePosition() - self.parent.GetPos()
            mouse_dist = mouse_dir.Length()
            mouse_dir = mouse_dir.Normalize()
            self.charge_time = 0.0
            self.can_shoot = False
            #print "Custo =", cost
            return self.Shoot(mouse_dir, mouse_dist, power, cost)
        return active

    def GetPower(self):
        return GetEquivalentValueInRange(self.charge_time, [0, self.max_charge_time], self.power_range)

    def GetEnergyCost(self, power, mult=-1 ):
        if self.charge_time <= 0:   return 0
        cost = self.shot_cost * (1 + (power * self.charge_time)) #basic shot cost
        cost = cost + (cost*self.parent.data.homing) # counting homing per shot
        if mult == -1:    mult = self.parent.data.GetNumShots()
        cost = cost *  (1+mult/14.0) #(mult + 1)/2.0   # counting multiplicity
        return cost

    def Shoot(self, direction, target_distance, power, cost):
        #checking energy cost
        if self.parent.energy < cost:    return False
        self.parent.TakeEnergy(cost)
        # calculating index for all shots
        N = self.parent.data.GetNumShots()
        #creating shots...
        for pos, vel in GetMultiShotData(N, self.parent, direction, target_distance, power, self.projectile_speed):
            #create projectile and set it up
            proj = Projectile(pos.get_x(), pos.get_y(), vel, power, self.parent.data.pulse_damage, True)
            proj.SetParent(self.parent)
            proj.SetTrackingTarget(self.target, self.parent.data.homing)
            proj.node.modifier().set_color( Color(0.0, 0.5, 1.0, 0.9) )
            proj.hitsFriendlyToParent = False
            proj.wraps_around_boundary = False
            AddNewObjectToScene(proj)
        #ending with a bang
        PlaySound("fire.wav")
        return True

#########
from Gravity import GravityWell

class AntiGravShield(GravityWell, Weapon):
    def __init__(self, energyCostPerSec):
        Weapon.__init__(self)
        self.energy_per_sec = energyCostPerSec
        GravityWell.__init__(self, 0, 0, 1)
        self.is_antigrav = True
    
    def Activate(self, parent):
        Weapon.Activate(self, parent)
        self.SetBaseRadius(parent.radius)
        self.mass *= 10
        self.AddIDToIgnoreList(parent.id)
        AddNewObjectToScene(self)

    def Toggle(self, active, dt):
        if active and not self.active:
            if self.parent.energy > self.energy_per_sec*0.5:
                self.active = active
        else:
            self.active = active
        self.HandleLowEnergyShutdown()
        return self.active

    def Update(self, dt):
        if self.parent.is_destroyed:
            self.Delete()
        else:
            GravityWell.Update(self, dt)
            self.SetPos( self.parent.GetPos() )
            if self.active and hasattr(self.parent, "energy"):
                if not self.HandleLowEnergyShutdown():
                    self.parent.TakeEnergy( self.energy_per_sec * dt )

    def HandleLowEnergyShutdown(self):
        if self.parent.energy < self.energy_per_sec*0.05:
            self.active = False
            return True
        return False

    def Dismantle(self):
        self.Delete()
        self.active = False

##########
class Laser(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.beam = None
        self.damage_per_sec = 200.0
        self.energy_per_sec = 40.0
        self.minimum_energy_required = 25.0 #minimum energy required for activation
        self.laser_width = 16.0

    def GetDamage(self):
        return self.damage_per_sec + self.parent.data.GetBonusDamage() + self.parent.data.GetNumShots()*10

    def Toggle(self, active, dt):
        energy_cost = self.energy_per_sec * dt
        if active and self.parent.energy >= energy_cost:
            if not self.beam:
                if self.parent.energy < self.minimum_energy_required:
                    return False
                self.beam = LaserBeam(self.parent, self.parent.GetDirection(), self.laser_width+self.parent.data.GetNumShots(), self.GetDamage() )
                AddNewObjectToScene(self.beam)
            self.beam.velocity = self.parent.GetDirection()
            #self.beam.SetBeamLength(self.parent.GetDirection().Length())
            self.parent.TakeEnergy(energy_cost)
            return True
        elif self.beam != None:
            self.beam.Delete()
            self.beam = None
        return False

    def Dismantle(self):
        if self.beam != None:
            self.beam.Delete()
            self.beam = None

##########
class ShockBomb(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.energy_cost = 50.0
        self.projectile_speed = 170.0
        self.shock_lifetime = 1.0
        self.shock_radius_range = [5.0, 180.0]
        self.can_shoot = True
        self.shock_damage = 80.0    # done once when shockwave hits a target
        self.wave_damage = 17.0      # done continously while shockwave pushes a target

    def GetShockDamage(self):
        return self.shock_damage + self.parent.data.GetBonusDamage()

    def GetWaveDamage(self):
        return self.wave_damage + self.parent.data.GetBonusDamage()/self.shock_damage

    def Toggle(self, active, dt):
        if active and self.can_shoot:
            self.can_shoot = False
            mouse_dir = Engine_reference().input_manager().GetMousePosition() - self.parent.GetPos()
            mouse_dist = mouse_dir.Length()
            mouse_dir = mouse_dir.Normalize()
            return self.Shoot(mouse_dir, mouse_dist)
        elif not active:
            self.can_shoot = True
        return False
 
    def Shoot(self, direction, target_dist):
        N = int(ceil(self.parent.data.GetNumShots()/2.0))
        if N == 0:  N = 1
        num_shots = 1
        cost = self.energy_cost

        for i in range(N-1):
            if self.parent.energy < cost+self.energy_cost*0.15:   break 
            num_shots += 1
            cost += self.energy_cost*0.2

        if self.parent.energy < cost:    return False
        self.parent.TakeEnergy(cost)
        power = 1.0

        for pos, vel in GetMultiShotData(num_shots, self.parent, direction, target_dist, power, self.projectile_speed):
            proj = Projectile(pos.get_x(), pos.get_y(), vel, power, 10.0, True)
            proj.SetParent(self.parent)
            proj.hitsFriendlyToParent = False
            proj.AddOnHitEvent(self.WarheadDetonation)
            proj.node.modifier().set_color( Color(1.0, 1.0, 0.1, 1.0) )
            AddNewObjectToScene(proj)
        PlaySound("fire.wav")
        return True

    def WarheadDetonation(self, projectile, target):
        pos = projectile.GetPos()
        wave = Shockwave.Shockwave(pos.get_x(), pos.get_y(), self.shock_lifetime, self.shock_radius_range)
        wave.shock_damage = self.GetShockDamage()
        wave.wave_damage = self.GetWaveDamage()
        wave.shock_force_factor = 0.05
        wave.AddIDToIgnoreList(self.parent.id)
        AddNewObjectToScene(wave)

#########
class Blackhole(Weapon):
    def __init__(self, energy_per_sec):
        Weapon.__init__(self)
        self.energy_per_sec = energy_per_sec
        self.firing = False
        self.blackhole = None

    def Toggle(self, active, dt):
        energy_cost = self.energy_per_sec * dt
        if active and (not self.firing) and self.parent.energy >= 2*self.energy_per_sec:
            self.firing = True
            self.hole_pos = Engine_reference().input_manager().GetMousePosition()
            self.parent.TakeEnergy(self.energy_per_sec)
            self.blackhole = Gravity.Blackhole(self.hole_pos.get_x(), self.hole_pos.get_y(), 50.0, 0)
            self.blackhole.AddIDToIgnoreList(self.parent.id)
            beam = VisualBeam(self.parent, self.blackhole, 10, Color(0.1,0.3,0.3, 0.7))
            AddNewObjectToScene(beam)
            AddNewObjectToScene(self.blackhole)
            return True
        elif active and self.firing:
            if self.parent.energy < energy_cost:
                self.firing = False
                self.blackhole.Delete()
                self.blackhole = None
                return False
            self.parent.TakeEnergy(energy_cost)
            return True
        elif not active:
            if self.firing:
                self.blackhole.Delete()
                self.blackhole = None
            self.firing = False
        return False

    def Dismantle(self):
        if self.blackhole != None:
            self.blackhole.Delete()
            self.blackhole = None

#########
class Hyperspace(Weapon):
    def __init__(self):
        Weapon.__init__(self)
        self.energy_cost = 35.0
        self.cooldown = 1.5
        self.time_elapsed = 0.0
        self.enabled = True
        self.engaged = False
        self.multi_jumps = 0
        self.multi_jump_counter = 0.0
        self.multi_jump_limit = 0.5

    def Toggle(self, active, dt):
        if self.enabled:
            if self.multi_jumps > 0:
                self.multi_jump_counter += dt
            jumped = False
            if active and not self.engaged:
                mouse_pos = Engine_reference().input_manager().GetMousePosition()
                self.multi_jump_counter = 0.0
                if self.multi_jumps == 0:
                    self.multi_jumps = self.parent.data.GetNumShots()
                    if self.parent.energy < self.energy_cost:    return False
                    self.parent.TakeEnergy(self.energy_cost)
                    #print "Started JUMP Chain!", self.multi_jumps
                self.multi_jumps -= 1
                if self.multi_jumps == 0:
                    self.multi_jump_counter += self.multi_jump_limit+1
                    #print "Finished JUMP Chain..."
                else:
                    self.multi_jump_counter = 0.0
                    #print "Jumped!"
                jumped = self.Engage(mouse_pos)
                self.engaged = True
            elif not active:
                self.engaged = False

            if self.multi_jump_counter > self.multi_jump_limit:
                self.multi_jump_counter = 0.0
                self.multi_jumps = 0
                self.enabled = False
                #print "Hyperspace is offline - cooldown"
            return jumped
        else:
            self.time_elapsed += dt
            if self.time_elapsed > self.cooldown:
                self.enabled = True
                self.time_elapsed = 0.0
                #print "Hyperspace ONLINE!"
        return False

    def GetDepartingShockwaveDmg(self):
        shock = 20.0 + self.parent.data.GetBonusDamage()
        wave = 12.0 + self.parent.data.GetBonusDamage()/20.0
        return (shock, wave)

    def GetArrivingShockwaveDmg(self):
        shock = 10.0 + self.parent.data.GetBonusDamage()/2.0
        wave = 1.0 + self.parent.data.GetBonusDamage()/20.0
        return (shock, wave)

    def Engage(self, pos):
        dep_dmgs = self.GetDepartingShockwaveDmg()
        dep_ranges = [self.parent.radius*2, 15.0]
        self.CreateShockwave(0.7, dep_ranges, dep_dmgs[0], dep_dmgs[1], -0.5, Color(1.0,0.2,0.2, 0.5)) # slow, small range, more damage
        self.parent.SetPos(pos)
        arr_dmgs = self.GetArrivingShockwaveDmg()
        arr_ranges = [self.parent.radius, self.parent.radius*4]
        self.CreateShockwave(1.0, arr_ranges, arr_dmgs[0], arr_dmgs[1], 1.0, Color(0.8,0.8,0.8, 0.5)) # fast, medium range, low damage pushes stuff
        return True

    def CreateShockwave(self, lifetime, radius_range, shock_dmg, wave_dmg, force_factor, color):
        pos = self.parent.GetPos()
        wave = Shockwave.Shockwave(pos.get_x(), pos.get_y(), lifetime, radius_range)
        wave.shock_damage = shock_dmg
        wave.wave_damage = wave_dmg
        wave.shock_force_factor = force_factor
        wave.node.modifier().set_color(color)
        wave.AddIDToIgnoreList(self.parent.id)
        AddNewObjectToScene(wave)

###################################################################################
###################################################################################
class FractalShot(Projectile):
    def __init__(self, x, y, velocity, depth):
        power = 0.8 + random()*0.4
        Projectile.__init__(self, x, y, velocity, power, 30.0, True)
        self.depth = depth
        self.node.modifier().set_color( Color(random(), random(), random(), 1.0) )
        self.AddOnHitEvent(self.Detonation)

    def Detonation(self, projectile, target):
        if self.depth <= 1: return
        numshots = randint(2,5)
        for i in range(numshots):
            pos = self.GetPos()
            dir = Vector2D(1.0, 0.0)
            dir = dir.Rotate(random()*2*pi)
            dir = dir * (self.radius*2)
            pos = pos + dir
            dir = dir.Normalize()
            dir = dir *( self.velocity.Length() )
            shot = FractalShot(pos.get_x(), pos.get_y(), dir, self.depth-1)
            shot.SetParent(self.parent)
            shot.hitsFriendlyToParent = False
            AddNewObjectToScene(shot)

######
from ugdk.ugdk_drawable import Sprite
from ugdk.ugdk_action import Observer
from ugdk.pyramidworks_collision import CollisionObject
from ugdk.pyramidworks_geometry import ConvexPolygon

class LaserBeam(EntityInterface,Observer):
    def __init__(self, parent, velocity, beam_width, damage_per_sec):
        EntityInterface.__init__(self, 0, 0, 1.0)
        self.sprite = Sprite("laser", "animations/laser.gdd")
        self.sprite.SelectAnimation("BASIC_LASER")
        self.sprite.AddObserverToAnimation(self)
        self.node.set_drawable(self.sprite)
        self.node.set_zindex(-1.0)
        self.velocity = velocity
        self.beam_width = beam_width
        self.beam_length = Engine_reference().video_manager().video_size().Length()
        self.parent = parent
        self.damage_per_sec = damage_per_sec
        self.delta_t = 0.0
        
        scaleX = self.beam_length / self.sprite.size().get_x()
        scaleY = self.beam_width / self.sprite.size().get_y()
        self.node.modifier().set_scale( Vector2D(scaleX, scaleY) )

        self.node.modifier().set_rotation(pi/2.0)                               ### comment these functions to make the entity's node
        self.node.modifier().set_offset( Vector2D(0.0, -self.beam_length/2.0) ) ### be a child of the scene
        self.parent.node.AddChild(self.node)                                    ### 
        
        self.setupCollisionObject()

    def setupCollisionObject(self):
        self.collision_object = CollisionObject(getCollisionManager(), self)
        self.collision_object.InitializeCollisionClass("Beam")
        self.geometry = ConvexPolygon(self.GetVertices())
        self.collision_object.set_shape(self.geometry)
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )
        self.collision_object.thisown = 0

    def GetNode(self):  return None      ### comment these functions to make the entity's node
    def GetHUDNode(self):   return None  ### be a child of the scene

    def SetBeamLength(self, length):
        self.beam_length = length
        self.UpdateModifier()

    def SetBeamWidth(self, width):
        self.beam_width = width
        self.UpdateModifier()

    def GetVertices(self):
        pos = self.parent.GetPos()
        dir = self.GetDirection()
        sideDir = Vector2D(-dir.get_y(), dir.get_x())
        sideDir = sideDir * (self.beam_width/2.0)
        v1 = pos + sideDir
        v4 = pos + (sideDir * -1)
        offset = dir * self.beam_length
        v2 = v1 + offset
        v3 = v4 + offset

        return Vector2DList([v1, v2, v3, v4])

    def UpdateModifier(self):
        scaleX = self.beam_length / self.sprite.size().get_x()
        scaleY = self.beam_width / self.sprite.size().get_y()
        self.node.modifier().set_scale( Vector2D(scaleX, scaleY) )
        self.node.modifier().set_offset( Vector2D(0.0, -self.beam_length/2.0) )

    def UpdateVertices(self):
        self.geometry.set_vertices(self.GetVertices())

    def Update(self, dt):
        if self.parent.is_destroyed:
            self.parent.node.RemoveChild(self.node)
            self.Delete()
            return

        self.delta_t = dt
        #self.node.modifier().set_rotation(self.GetDirection().Angle() + pi/2.0)                              ### uncomment these lines to make the entity's node
        #self.node.modifier().set_offset( self.parent.GetPos() + (self.GetDirection()*self.beam_length/2.0) ) ### be a child of the scene
        self.UpdateVertices()

    def GetDirection(self):
        if self.velocity.Length() == 0.0:
            return Vector2D(0.0, 1.0)
        return self.velocity.Normalize()

    def Tick(self):
        pass

    def createExplosionForTarget(self, target):
        pos = self.parent.GetPos()
        dir = self.GetDirection() * ( (target.GetPos() - pos).Length() - target.radius )
        pos = pos + dir
        dir = target.GetPos() - pos
        pos = pos + (dir.Normalize() * self.beam_width/2.0)
        explosion = CreateExplosionAtLocation(pos, self.beam_width)
        AddNewObjectToScene(explosion)

    def HandleCollision(self, target):
        if hasattr(target, "GetGroup") and target.GetGroup() != self.parent.GetGroup() and target.GetGroup() != Group.NEUTRAL:
            target.TakeDamage(self.damage_per_sec * self.delta_t)
            self.createExplosionForTarget(target)
        elif target.CheckType("Planet"):
            target.TakeDamage(self.damage_per_sec * self.delta_t / 2.0)
            self.createExplosionForTarget(target)


class VisualBeam(EntityInterface):
    def __init__(self, ent1, ent2, beam_width, color):
        EntityInterface.__init__(self, 0, 0, 1.0)
        self.sprite = Sprite("laser", "animations/laser.gdd")
        self.sprite.SelectAnimation("BASIC_LASER")
        self.node.set_drawable(self.sprite)
        self.node.modifier().set_color(color)
        self.node.set_zindex(-1.0)
        self.beam_width = beam_width
        self.ents = (ent1, ent2)
        self.is_collidable = False
        
    def SetBeamWidth(self, width):
        self.beam_width = width

    def UpdateModifier(self):
        dir = self.ents[1].GetPos() - self.ents[0].GetPos()
        beam_length = dir.Length()

        self.node.modifier().set_rotation(-dir.Angle())

        scaleX = beam_length / self.sprite.size().get_x()
        scaleY = self.beam_width / self.sprite.size().get_y()
        self.node.modifier().set_scale( Vector2D(scaleX, scaleY) )

        dir = dir.Normalize() * beam_length/2.0
        dir = self.ents[0].GetPos() + dir
        self.node.modifier().set_offset( dir )

    def Update(self, dt):
        if self.ents[0].is_destroyed or self.ents[1].is_destroyed:
            self.Delete()
            return
        self.UpdateModifier()

    def HandleCollision(self, target):
        pass
