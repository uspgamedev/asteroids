from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Color
from BasicEntity import BasicEntity, CalculateAfterSpeedBasedOnMomentum
from Animations import CreateExplosionFromCollision
from Weapons import Turret
from ItemFactory import CreatePowerUp
from random import random, randint, shuffle
from math import pi

class Asteroid (BasicEntity):
    @staticmethod
    def GetActualRadius(size_factor):
        return 30.0 * size_factor

    @staticmethod
    def GetTurretCooldown(size_factor):
        return 1.0/size_factor

    @staticmethod
    def CheckChanceForTurret(size_factor):
        chance = size_factor/2.0  #2.0 here is the (approximate?) maximum Asteroid sizeFactor in difficulty 1
        return random() < chance

    def __init__(self, x, y, size_factor):
        self.size_factor = size_factor
        r = Asteroid.GetActualRadius(size_factor)
        hp = 120 * size_factor
        BasicEntity.__init__(self, x, y, "images/asteroid%s.png" % (randint(1,3)), r, hp)
        angle = random() * 2 * pi
        for node in self.nodes:
            node.modifier().set_rotation( angle )
        self.has_splitted = False
        self.mass = 1000.0 + 100000000*size_factor
        self.collidedWithAsteroids = []
        self.diedFromPlanet = False
        self.turret = None
        if Asteroid.CheckChanceForTurret(size_factor):
            self.turret = Turret(self, "Ship", Asteroid.GetTurretCooldown(size_factor), 70, 0.4, Color(1.0, 0.0, 0.3, 1.0))
        
    def Update(self, dt):
        BasicEntity.Update(self, dt)
        if self.turret != None:
            self.turret.Update(dt)
        self.collidedWithAsteroids = []

    def TakeDamage(self, damage):
        BasicEntity.TakeDamage(self, damage)
        # if we're big enough, split asteroid when we are destroyed.
        if self.is_destroyed:
            self.Break()

    def Break(self):
        if self.size_factor > 0.4 and not self.has_splitted:
            self.has_splitted = True
            angles = [0.0, -pi/4.0, -pi/2.0, -3*pi/2.0, pi, 3*pi/2.0, pi/2.0, pi/4.0]
            shuffle(angles)
            direction = self.velocity.Normalize()
            pieceNumber = randint(2,3)
            factor = self.size_factor / 1.5
            #print self, "is splitting, into factor", factor
            for i in range(pieceNumber):
                v = direction.Rotate(angles.pop())
                v = v * ((self.radius+Asteroid.GetActualRadius(factor))*1.15)
                pos = self.GetPos() + v
                ast = Asteroid(pos.get_x(), pos.get_y(), factor)
                v = v.Normalize()
                speed = self.velocity.Length()
                v = v * (randint(int(speed*0.60), int(speed*1.40)))
                ast.ApplyVelocity(v)
                self.new_objects.append(ast)
            ###
            lifepack = CreatePowerUp(self.GetPos().get_x(), self.GetPos().get_y())
            self.new_objects.append(lifepack)
            self.is_destroyed = True

    def GetDamage(self, obj_type):
        if obj_type == self.type:
            return self.life * 0.2
        return self.life

    def GetPointsValue(self):
        if self.diedFromPlanet: return 0
        v = self.max_life
        if self.turret != None: v += 100
        return v

    def HandleCollision(self, target):
        #print "%s IS COLLIDING WITH %s" % (self, target)
        if target.CheckType("Asteroid") and not target.id in self.collidedWithAsteroids:
            target.collidedWithAsteroids.append(self.id)
            
            self.ApplyCollisionRollback()
            target.ApplyCollisionRollback()
            aux = self.velocity
            after_speeds = CalculateAfterSpeedBasedOnMomentum(self, target)
            self.velocity = target.velocity.Normalize()
            target.velocity = aux.Normalize()
            sf = 1.0
            tf = 1.0
            if after_speeds[0] > 80.0:
                st= 0.7
            if after_speeds[1] > 80.0:
                tf = 0.7 
            self.velocity = self.velocity * (after_speeds[0]*sf)
            target.velocity = target.velocity * (after_speeds[1]*tf)

            #self.velocity = target.velocity
            #target.velocity = aux

            self.TakeDamage(target.GetDamage(self.type))
            target.TakeDamage(self.GetDamage(target.type))
            CreateExplosionFromCollision(self, target, self.radius*0.7)
            #print "Asteroid collided with asteroid"
        elif target.CheckType("Ship"):
            target.TakeDamage(self.GetDamage(target.type))
            target.ApplyVelocity(self.velocity * 0.5)
            self.TakeDamage(self.life + 10) #just to make sure we die and split LOL
            CreateExplosionFromCollision(self, target, (self.radius+target.radius)/2.0)
            #print "Asteroid damaging ", target.type
        elif target.CheckType("Planet"):
            target.TakeDamage(self.GetDamage(target.type))
            self.is_destroyed = self.has_splitted = True # WE CANNOT SPLIT when colliding with a planet =P
            CreateExplosionFromCollision(self, target, target.radius*1.2)
            self.diedFromPlanet = True
            #print "Asteroid damaging ", target.type
        elif target.CheckType("Satellite"):
            target.TakeDamage(self.GetDamage(target.type))
            self.TakeDamage(self.life + 10) #just to make sure we die and split LOL
            CreateExplosionFromCollision(self, target, (self.radius+target.radius)/2.0)

        #No handler for projectile since that is strictly
        #"do it only one time", and Projectile will handle it
