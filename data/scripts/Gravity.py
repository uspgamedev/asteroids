from ugdk.ugdk_math import Vector2D
from ugdk.pyramidworks_collision import CollisionObject, CollisionLogic
from ugdk.pyramidworks_geometry import Circle
from ugdk.ugdk_base import Engine_reference
from ugdk.ugdk_drawable import TexturedRectangle
from ugdk.ugdk_graphic import Drawable
from BasicEntity import EntityInterface, BasicColLogic, getCollisionManager
from random import randint, shuffle
from math import pi
import Config

# Factor to which multiply the gravity force.
# just a configurational value to fine tune the gravity, in case you want
# it stronger or weaker.
GRAVITY_FACTOR = 50.0

#density --> in g/cm^3, default is 5.515  (Earth's density)
DEFAULT_DENSITY = 5.515

####################################
# this is going to be nice :D
# just like old times.
# back to the roots you know?
# roots and branches...
# Jethro Tull? O_o
class GravityWell (EntityInterface):
    def __init__(self, x, y, planet_radius):
        self.mass = GetMassByRadius(planet_radius)
        r = GetMaxGravForceDist(self.mass)
        EntityInterface.__init__(self, x, y, r)
        self.is_antigrav = False
        self.ignore_ids = []
        self.active = True
        self.delta_t = 0.0
        self.collision_object = CollisionObject(getCollisionManager(), self)  #initialize collision object, second arg is passed to collisionlogic to handle collisions
        self.collision_object.InitializeCollisionClass("Gravity")              # define the collision class
        self.geometry = Circle(self.radius)                           #
        self.collision_object.set_shape(self.geometry)                # set our shape
        #finally add collision logics to whatever collision class we want
        self.collision_object.AddCollisionLogic("Entity", BasicColLogic(self) )

    def SetBaseRadius(self, r):
        self.mass = GetMassByRadius(r)
        rmax = GetMaxGravForceDist(self.mass)
        self.radius = rmax
        self.geometry.set_radius(rmax)

    def ToggleActive(self):
        self.active = not self.active

    def AddIDToIgnoreList(self, ID):
        if ID not in self.ignore_ids:
            self.ignore_ids.append(ID)
            
    def RemoveIDFromIgnoreList(self, ID):
        if ID in self.ignore_ids:
            self.ignore_ids.remove(ID)

    def Update(self, dt):
        EntityInterface.Update(self, dt)
        self.delta_t = dt

    def HandleCollision(self, target):
        ignore_types = ["Planet"]
        if not self.active or target.type in ignore_types or target.id in self.ignore_ids:
            return #we don't affect planets (neither their wells)
        
        grav_vec = self.GetPos() - target.GetPos()
        dist = grav_vec.Length()

        GravForce = GetGravForce(self.mass, dist)

        grav_vec = grav_vec.Normalize()
        if self.is_antigrav:
            grav_vec = grav_vec * -1

        # GravForce is in pixels/hr^2,  self.delta_t is in secs
        # GravForce * (1 / (3600**2)) will convert it to pixels/sec^2
        grav_vec = grav_vec * GravForce * self.delta_t *100

        target.ApplyVelocity(grav_vec)
        
class Blackhole (GravityWell):
    def __init__(self, x, y, radius, lifetime):
        GravityWell.__init__(self, x, y, radius)
        self.mass = GetMassByRadius(radius, 150.0)
        self.radius = Config.gamesize.Length()
        self.geometry.set_radius(self.radius)
        self.lifetime = lifetime
        self.elapsed_time = 0.0
        self.hole_radius = radius
        self.angle = 0.0
        self.size = Vector2D(self.hole_radius*2, self.hole_radius*2)
        texture_obj = Engine_reference().resource_manager().texture_container().Load("images/blackhole.png", "images/blackhole.png")
        self.shape = TexturedRectangle( texture_obj, self.size )
        self.shape.set_hotspot(Drawable.CENTER)
        self.node.set_drawable(self.shape)

    def Update(self, dt):
        GravityWell.Update(self, dt)
        self.angle += dt * pi
        if self.angle > 2*pi:   self.angle -= 2*pi
        self.node.modifier().set_rotation(self.angle)
        if self.lifetime > 0:
            self.elapsed_time += dt
            if self.elapsed_time > self.lifetime:
                self.Delete()
    
    def HandleCollision(self, target):
        target_dist = (self.GetPos() - target.GetPos()).Length()
        if target.CheckType("Planet"):
            target.TakeDamage(0.25 * ((self.radius-target_dist)/self.radius))
        GravityWell.HandleCollision(self, target)
        if not target.id in self.ignore_ids and target_dist < self.hole_radius:
            if target.CheckType("Asteroid"):
                target.velocity = target.velocity * 0.1
            target.TakeDamage(target.life + 10)
         
########
################################################################
#  The Gravity Constant
###
# Constant variable used in various gravity force related calculations
# - Real Physics value - don't change.
################################################################
GRAVITY_CONSTANT = 6.67e-017

################################################################
###    GetGravForce
# Theoretically, plamass is in Kilograms and distance in Kilometers
# then the return is in km/h^2 (wihout the /3.6 -> return em m/s^2)
##
# speaking theoretically since in this game we are not really
# using units other than 'pixels'... 
# So we will just assume that all 'masses' are in Kg and
# pixels <=> kilometers :D
################################################################
def GetGravForce(plamass, distance):
    force = (GRAVITY_CONSTANT * plamass * GRAVITY_FACTOR) / (distance**2)
    return force/3.6

######################################################
# GetMassByRadius
#radius --> in Km 
#density --> in g/cm^3, default is 5.515  (Earth's density)
#return ==> mass in Kg
################################################################
def GetMassByRadius(radius, density = -1):
    if density == -1:   density = DEFAULT_DENSITY
    densityConversionConst = 10**12
    nKesph = 4.0/3.0
    vol = nKesph * pi * (radius**3)
    mass = (density*densityConversionConst)*vol
    return mass
    
################################################################
##    GetMaxGravForceDist
#return in kilometers
#the distance from the planet with given mass that the gravity force will be 0.1m/s^2  (0.02km/h^2)
#App.UtopiaModule_ConvertGameUnitsToKilometers()
################################################################
def GetMaxGravForceDist(plamass):
	if plamass > 0:
		dkm = (GRAVITY_CONSTANT * plamass * GRAVITY_FACTOR * 10) ** 0.5 #yes, we elevate to 0.5 to do sqrt() =P
		return dkm
	return 0
