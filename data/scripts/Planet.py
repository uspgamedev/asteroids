from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Engine_reference
from BasicEntity import BasicEntity, AddNewObjectToScene
from Asteroid import Asteroid
from Gravity import GravityWell
from Shockwave import Shockwave
from Animations import CreateExplosionFromCollision
import Config
from random import random, randint, shuffle
from math import pi, cos


# yes, Planet is pretty similar to Asteroid... But, whatever =P
class Planet (BasicEntity):
    def __init__(self, x, y, size_factor):
        self.size_factor = size_factor
        df = Engine_reference().CurrentScene().difficultyFactor
        r = 75.0 * size_factor
        hp = 600 * size_factor
        hp += hp*(df/100.0)
        BasicEntity.__init__(self, x, y, "images/planet%s.png" % (randint(1,5)), r, hp)
        self.has_splitted = False
        self.well = GravityWell(x, y, r)
        self.well.AddIDToIgnoreList(self.id)
        AddNewObjectToScene(self.well)
        
    def Update(self, dt):
        BasicEntity.Update(self,dt)
        self.well.SetPos( self.GetPos() )

    def TakeDamage(self, damage):
        BasicEntity.TakeDamage(self, damage)
        # if we're big enough, split planet into asteroids when we are destroyed.
        if self.is_destroyed and not self.has_splitted:
            self.has_splitted = True
            self.well.Delete() #to assure our gravity well will be deleted with us
            # produce our shockwave before the asteroids since the C++ part pop()'s the objects
            # out of the list, so last objects in self.new_objects are created first.
            pos = self.GetPos()
            #print "Planet cracking down..."
            wave = Shockwave(pos.get_x(), pos.get_y(), 4.0, [self.radius, Config.gamesize.Length() * 0.35])
            wave.AddIDToIgnoreList(self.id)
            AddNewObjectToScene(wave)
            #print "Shockwave created"
            # and create our 'asteroid parts'
            angles = [0.0, -pi/4.0, -pi/2.0, -3*pi/2.0, pi, 3*pi/2.0, pi/2.0, pi/4.0]
            shuffle(angles)
            direction = Vector2D(1,0).Rotate(random()*2*pi)
            direction = direction.Normalize()
            factor = 0.75
            #print self, "is breaking, into factor", factor
            scene = Engine_reference().CurrentScene()
            for i in range(randint(2,5)):
                v = direction.Rotate(angles.pop())
                if hasattr(scene, "hero") and scene.hero != None and not scene.hero.is_destroyed:
                    toHero = scene.hero.GetPos() - self.GetPos()
                    if toHero.Length() < self.radius*3 + scene.hero.radius:
                        while cos(pi/4.0) < (toHero.Normalize()*v) <= 1.0:
                            v = direction.Rotate(angles.pop())

                v = v * ((self.radius+Asteroid.GetActualRadius(factor))*0.5)
                pos = pos + v
                ast = Asteroid(pos.get_x(), pos.get_y(), factor)
                v = v.Normalize()
                speed = 50.0
                v = v * (randint(int(speed*0.60), int(speed*1.40)))
                ast.ApplyVelocity(v)
                AddNewObjectToScene(ast)

    def GetDamage(self, obj_type):
        return 9000.1 # Vegeta, what does the scouter say about his power level?

    def GetPointsValue(self):
        return -self.max_life*2

    def HandleCollision(self, target):
        if target.CheckType("Planet"):
            #print "WTF dude, u tripping? Planets colliding with planets? Ya frakking nuts?"
            aux = self.velocity
            self.velocity = target.velocity
            target.velocity = aux
            self.ApplyCollisionRollback()
            target.ApplyCollisionRollback()
        elif target.CheckType("Ship"):
            CreateExplosionFromCollision(self, target, target.radius*2)
            is_invul = target.invulnerable
            target.invulnerable = False
            target.TakeDamage(self.GetDamage(target.type))
            target.invulnerable = is_invul
            #print target.type, "crash landed on Planet... No survivors.     Boo-hoo."
        # Projectiles and Asteroids take care of collising with Planets.

