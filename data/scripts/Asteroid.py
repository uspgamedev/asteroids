from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Color, Engine_reference
from BasicEntity import BasicEntity, Group, CalculateAfterSpeedBasedOnMomentum, SeparateVectorComponents, AddNewObjectToScene
from Animations import CreateExplosionFromCollision
from Weapons import Turret
from ItemFactory import CreatePowerUp
import Config
from random import random, randint, shuffle
from math import pi, cos

class Asteroid (BasicEntity):
    BASE_RADIUS = 30.0
    @staticmethod
    def GetActualRadius(size_factor):
        return Asteroid.BASE_RADIUS * size_factor

    @staticmethod
    def GetMaximumFactor():
        return (Config.MAX_ENTITY_SIZE/2.0) / Asteroid.BASE_RADIUS

    @staticmethod
    def GetTurretCooldown(size_factor):
        return 

    @staticmethod
    def CheckChanceForTurret(size_factor):
        chance = size_factor/2.0  #2.0 here is the (approximate?) maximum Asteroid sizeFactor in difficulty 1
        return random() < chance

    def __init__(self, x, y, size_factor):
        if size_factor > Asteroid.GetMaximumFactor():
            size_factor = Asteroid.GetMaximumFactor()
        r = Asteroid.GetActualRadius(size_factor)
        self.size_factor = size_factor
        df = Engine_reference().CurrentScene().difficultyFactor
        hp = 120 * size_factor
        if df > 2:  hp += hp*(df/25.0)
        BasicEntity.__init__(self, x, y, "images/asteroid%s.png" % (randint(1,3)), r, hp)
        self.group = Group.ASTEROIDS
        angle = random() * 2 * pi
        self.rotation_speed = 0
        if random() > 0.2: 
            self.rotation_speed = random()*pi - pi/2
        self.node.modifier().set_rotation( angle )
        self.has_splitted = False
        self.mass = 1000.0 + 100000000*size_factor
        self.collidedWithAsteroids = []
        self.diedFromPlanet = False
        self.turret = None
        if Asteroid.CheckChanceForTurret(size_factor):
            if df > 110:    df = 110.0
            cooldown = 2.7 - (size_factor/Asteroid.GetMaximumFactor()) - df/100 - random()*0.5
            speed = 80 + df
            power = 0.3 + random()*(size_factor/Asteroid.GetMaximumFactor())
            self.turret = Turret(self, "Ship", cooldown, speed, power, Color(1.0, 0.0, 0.3, 1.0))
        
    def Update(self, dt):
        BasicEntity.Update(self, dt)
        angle = self.node.modifier().rotation()
        angle += self.rotation_speed * dt
        if angle > 2*pi:    angle -= 2*pi
        self.node.modifier().set_rotation(angle)
        if self.turret != None:
            self.turret.Update(dt)
        self.collidedWithAsteroids = []

    def Break(self):
        if self.size_factor > 0.4 and not self.has_splitted:
            self.has_splitted = True
            angles = [0.0, -pi/4.0, -pi/2.0, -3*pi/2.0, pi, 3*pi/2.0, pi/2.0, pi/4.0]
            shuffle(angles)
            direction = self.velocity.Normalize()
            pieceNumber = randint(2,3)
            factor = self.size_factor / 1.75
            #print self, "is splitting, into factor", factor
            scene = Engine_reference().CurrentScene()
            for i in range(pieceNumber):
                v = direction.Rotate(angles.pop())
                if hasattr(scene, "hero") and scene.hero != None and not scene.hero.is_destroyed:
                    toHero = scene.hero.GetPos() - self.GetPos()
                    if toHero.Length() < self.radius*3 + scene.hero.radius:
                        while cos(pi/4.0) < (toHero.Normalize()*v) <= 1.0:
                            v = direction.Rotate(angles.pop())

                v = v * ((self.radius+Asteroid.GetActualRadius(factor))*1.15)
                pos = self.GetPos() + v
                ast = Asteroid(pos.get_x(), pos.get_y(), factor)
                v = v.Normalize()
                speed = self.velocity.Length()
                v = v * speed*(0.6+random()*0.6)
                ast.ApplyVelocity(v)
                AddNewObjectToScene(ast)
            ###
            df = scene.difficultyFactor
            plus = 0.5 * (self.size_factor / Asteroid.GetMaximumFactor()  -  df/200)
            chance = Config.baseDropRate + plus
            if random() <= chance:
                itempack = CreatePowerUp(self.GetPos().get_x(), self.GetPos().get_y())
                AddNewObjectToScene(itempack)
            self.Delete()

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
            CreateExplosionFromCollision(self, target, self.radius*0.7)


            #print "selfVelocity(%s, %s) :: targetVelocity(%s, %s)" % (self.velocity.get_x(), self.velocity.get_y(), target.velocity.get_x(), target.velocity.get_y())

            collision_line = (self.GetPos() - target.GetPos()).Normalize()
            selfV = SeparateVectorComponents(self.velocity, collision_line)
            targetV = SeparateVectorComponents(target.velocity, collision_line)
            after_speeds = CalculateAfterSpeedBasedOnMomentum(selfV[0].Length(), self.mass, targetV[0].Length(), target.mass, random())

            plusToTarget = selfV[0] - selfV[0].Normalize()*after_speeds[0]
            plusToSelf = targetV[0] - targetV[0].Normalize()*after_speeds[1]

            #print "PlusToTarget(%s, %s) :: PlusToSelf(%s, %s)" % (plusToTarget.get_x(), plusToTarget.get_y(), plusToSelf.get_x(), plusToSelf.get_y())

            self.velocity = targetV[0].Normalize()*after_speeds[0] + selfV[1] #+ plusToSelf
            target.velocity = selfV[0].Normalize()*after_speeds[1] + targetV[1] # + plusToTarget
            #print "AFTER selfVelocity(%s, %s) :: targetVelocity(%s, %s)" % (self.velocity.get_x(), self.velocity.get_y(), target.velocity.get_x(), target.velocity.get_y())
            #print "-----------------"

            rotToTarget = self.rotation_speed * random()
            rotToSelf = target.rotation_speed * random()
            self.rotation_speed += rotToSelf - rotToTarget
            target.rotation_speed += rotToTarget - rotToSelf

            self.ApplyCollisionRollback()
            target.ApplyCollisionRollback()

            self.TakeDamage(target.GetDamage(self.type))
            target.TakeDamage(self.GetDamage(target.type))
            #print "Asteroid collided with asteroid"
        elif target.CheckType("Ship"):
            CreateExplosionFromCollision(self, target, (self.radius+target.radius)/2.0)
            target.TakeDamage(self.GetDamage(target.type))
            target.ApplyVelocity(self.velocity * 0.5)
            self.TakeDamage(self.life + 10) #just to make sure we die and split LOL
            #print "Asteroid damaging ", target.type
        elif target.CheckType("Planet"):
            CreateExplosionFromCollision(self, target, target.radius*1.2)
            target.TakeDamage(self.GetDamage(target.type))
            self.is_destroyed = self.has_splitted = True # WE CANNOT SPLIT when colliding with a planet =P
            self.diedFromPlanet = True
            #print "Asteroid damaging ", target.type
        elif target.CheckType("Satellite"):
            CreateExplosionFromCollision(self, target, (self.radius+target.radius)/2.0)
            target.TakeDamage(self.GetDamage(target.type))
            self.TakeDamage(self.life + 10) #just to make sure we die and split LOL
            

        #No handler for projectile since that is strictly
        #"do it only one time", and Projectile will handle it

    def Delete(self):
        if not self.is_destroyed:
            self.Break()
        BasicEntity.Delete(self)
