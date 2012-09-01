from ugdk.ugdk_math import Vector2D, Vector2DList
from ugdk.ugdk_base import Color, Engine_reference, ResourceManager_CreateTextFromLanguageTag
from ugdk.ugdk_input import InputManager, K_w, K_a, K_s, K_d, M_BUTTON_LEFT, K_ESCAPE, M_BUTTON_RIGHT
from ugdk.ugdk_graphic import Node
from ugdk.pyramidworks_geometry import ConvexPolygon
from BasicEntity import BasicEntity, Group, RangeCheck, GetEquivalentValueInRange
import Weapons
from BarUI import BarUI, BAR_SIZE
from Shockwave import Shockwave
from math import pi
from random import randint

class ShipData:
    def __init__(self, max_life, max_energy, energy_regen_rate, pulse_damage, pulse_shots, homing):
        self.max_life = max_life
        self.original_max_life = max_life
        self.max_energy = max_energy
        self.energy_regen_rate = energy_regen_rate
        self.pulse_damage = pulse_damage
        self.original_pulse_damage = pulse_damage
        self.pulse_shots = pulse_shots
        self.homing = homing

    def GetBonusDamage(self):
        return self.pulse_damage - self.original_pulse_damage

    def GetBonusLife(self):
        return self.max_life - self.original_max_life

    def GetNumShots(self):
        N = self.pulse_shots
        if N > 14:  N = 14
        return N

    def __repr__(self):
        return "{ShipData: [MaxLife=%s][MaxEnergy=%s][PulseDmg=%s][PulseShots=%s][Homing=%s]}" % (self.max_life, self.max_energy, self.pulse_damage, self.pulse_shots, self.homing)
    def __str__(self): return self.__repr__()
        

class Ship (BasicEntity):
    def __init__(self, x, y, data):
        self.image_w = 420.0
        self.image_h = 830.0
        BasicEntity.__init__(self, x, y, "images/ship.png", 20.0, data.max_life, self.image_h/self.image_w)
        self.radius = (self.size*0.5).Length()
        self.node.set_zindex(1.0)
        self.graphic_node = Node()
        self.node.set_drawable(None)
        self.graphic_node.set_drawable(self.shape)
        self.graphic_node.set_zindex(1.0)
        self.node.AddChild(self.graphic_node)
        self.group = Group.SHIP
        self.acceleration = Vector2D(0.0, 0.0)
        self.data = data
        self.max_energy = self.data.max_energy
        self.energy = self.max_energy
        self.bonus_regen_counter = 0.0
        self.bonus_regen_threshold = 3.0
        self.speed = 400.0                  # |acceleration| in a given frame
        self.max_speed = 200.0              # max |velocity| ship can attain.

        #self.rangeCheck = RangeCheck(0, 0, 1024.0, "Asteroid")
        #self.rangeCheck.AttachToEntity(self)

        self.pulse_weapon = Weapons.Pulse()
        self.right_weapon = None
        self.pulse_weapon.Activate(self)
        #self.right_weapon.Activate(self)

        offset = self.size.get_y()/2.0
        self.life_hud.SetOffset(offset)

        self.energy_hud = BarUI(self, "energy", Color(0.0,0.0,1.0,1.0), offset+BAR_SIZE)
        self.hud_node.AddChild(self.energy_hud.node)

        self.charge_hud = BarUI(self.pulse_weapon, "charge_time", Color(1.0,1.0,0.0,1.0), -offset-2*BAR_SIZE)
        self.hud_node.AddChild(self.charge_hud.node)

    def setupCollisionGeometry(self):
        self.geometry = ConvexPolygon(self.GetVertices())

    def GetVertices(self):
        pos = self.GetPos()
        dir = self.GetDirection().Normalize()
        sideDir = Vector2D(-dir.get_y(), dir.get_x())
        sideDir = sideDir * (self.size.get_x()/2.0)
        #middleL = pos + sideDir
        #middleR = pos + (sideDir * -1)
        middleL = sideDir
        middleR = (sideDir * -1)
        offset = dir * self.size.get_y()/2.0
        v1 = middleL + (offset*-1)
        v2 = middleL + offset
        v3 = middleR + offset
        v4 = middleR + (offset * -1)

        return Vector2DList([v1, v2, v3, v4])

    def UpdateVertices(self):
        self.geometry.set_vertices(self.GetVertices())

    def set_max_life(self, value):
        self.data.max_life = value
        self.max_life = value

    def set_max_energy(self, value):
        self.data.max_energy = value
        self.max_energy = value

    def RestoreEnergy(self, amount):
        if amount < 0:  return
        self.energy += amount
        if self.energy > self.max_energy:
            self.energy = self.max_energy

    def TakeEnergy(self, amount):
        if amount < 0:  return
        self.energy -= amount
        if self.energy < 0:
            self.energy = 0.0

    def SetRightWeapon(self, weapon):
        if self.right_weapon != None:
            self.right_weapon.Dismantle()
        self.right_weapon = weapon
        self.right_weapon.Activate(self)

    def GetDirection(self):
        return Engine_reference().input_manager().GetMousePosition() - self.GetPos()

    def Update(self, dt):
        self.CheckCommands(dt)
        self.UpdateVertices()
        self.velocity = self.velocity + (self.acceleration * dt)
        if (self.velocity.Length() > self.max_speed):
            self.velocity = self.velocity * (self.max_speed/self.velocity.Length())
        self.UpdatePosition(dt)
        self.life_hud.Update()
        self.energy_hud.Update()
        self.charge_hud.Update()
        self.CleanUpActiveEffects()

    def CheckCommands(self, dt):
        input = Engine_reference().input_manager()

        mouse_dir = input.GetMousePosition() - self.node.modifier().offset()
        mouse_dir = mouse_dir.Normalize()
        self.node.modifier().set_rotation( -(mouse_dir.Angle()+pi/2.0)  )
        accel = Vector2D(0.0, 0.0)
        ############
        #if input.KeyDown(K_w):
        #    accel += mouse_dir
        #if input.KeyDown(K_a):
        #    left = mouse_dir.Rotate(-pi/2.0)
        #    left = left.Normalize()
        #    accel += left
        #    accel = accel.Normalize()
        #if input.KeyDown(K_s):
        #    accel += -mouse_dir
        #    accel = accel.Normalize()
        #if input.KeyDown(K_d):
        #    right = mouse_dir.Rotate(pi/2.0)
        #    right = right.Normalize()
        #    accel += right
        #    accel = accel.Normalize()
        #############
        if input.KeyDown(K_w):
            accel += Vector2D(0.0, -1.0)
        if input.KeyDown(K_a):
            accel += Vector2D(-1.0, 0.0)
        if input.KeyDown(K_s):
            accel += Vector2D(0.0, 1.0)
        if input.KeyDown(K_d):
            accel += Vector2D(1.0, 0.0)
        accel = accel.Normalize()
        accel = accel * self.speed
        self.acceleration = accel

        #self.pulse_weapon.SetTarget( self.rangeCheck.GetTarget() )
        weaponFiring = self.pulse_weapon.Toggle(input.MouseDown(M_BUTTON_LEFT), dt)
        if self.right_weapon != None:
            weaponFiring = weaponFiring or self.right_weapon.Toggle(input.MouseDown(M_BUTTON_RIGHT), dt)

        if not weaponFiring:
            if self.energy < self.max_energy:
                self.RestoreEnergy(self.GetActualEnergyRegenRate() * dt)
            self.bonus_regen_counter += dt
        else:
            self.bonus_regen_counter = 0.0

    def GetActualEnergyRegenRate(self):
        regen_rate = self.data.energy_regen_rate
        if self.bonus_regen_counter > self.bonus_regen_threshold:
            regen_rate += self.data.energy_regen_rate*0.25*((self.bonus_regen_counter-self.bonus_regen_threshold)/self.bonus_regen_threshold)
        return regen_rate


    def HandleCollision(self, target):
        pass
        #other entities handle collision with Ship

###################

class Satellite(BasicEntity):
    def __init__(self, parent, life, starting_angle):
        self.parent = parent
        x = parent.GetPos().get_x()
        y = parent.GetPos().get_y()
        BasicEntity.__init__(self, x, y, "images/satellite.png", 10.0, life)
        self.orbit_angle = starting_angle
        self.angle_speed = pi/2.5  # angle speed in radians per second
        self.turret = Weapons.Turret(self, "Asteroid", 0.6, 170.0, 0.6, Color(0.0, 1.0, 0.1, 0.7))
        self.turret.hitsFriendlyToParent = False
        self.turret.hitsSameClassAsParent = False

    def CalculateOrbitPos(self):
        pos = self.parent.GetPos()
        direction = Vector2D(0, 1).Rotate(self.orbit_angle).Normalize()
        orbit = direction * (self.parent.radius*0.9 + self.radius)
        return orbit + pos

    def Update(self, dt):
        if self.parent.is_destroyed:
            self.Delete()
            return
        self.SetPos(self.CalculateOrbitPos() )
        self.orbit_angle += self. angle_speed * dt
        if self.orbit_angle > 2*pi:
            self.orbit_angle -= 2*pi
        self.velocity = self.parent.velocity
        self.turret.Update(dt)
        self.velocity *= 0.0
        BasicEntity.Update(self, dt)
        
    def HandleCollision(self, target):
        pass
