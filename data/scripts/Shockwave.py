from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Engine_reference
from ugdk.ugdk_drawable import TexturedRectangle
from ugdk.ugdk_graphic import Drawable
from Gravity import GravityWell, GetGravForce, GetMassByRadius
from BasicEntity import GetEquivalentValueInRange
from math import pi


class Shockwave (GravityWell):
    def __init__(self, x, y, lifetime, radius_range):
        self.max_lifetime = lifetime
        self.lifetime = 0.0
        self.radius_range = radius_range
        GravityWell.__init__(self, x, y, radius_range[0])
        self.radius = radius_range[0]
        self.geometry.set_radius(self.radius)
        self.is_antigrav = True
        self.size = Vector2D(self.radius*2, self.radius*2)
        texture_obj = Engine_reference().resource_manager().texture_container().Load("images/shockwave.png", "images/shockwave.png")
        for node in self.nodes:
            shape = TexturedRectangle( texture_obj, self.size )
            shape.set_hotspot(Drawable.CENTER)
            node.set_drawable(shape)
            node.modifier().set_alpha(0.5)
        self.scale_range = [1.0, radius_range[1]/radius_range[0]]
        self.affected_targets = []
        self.shock_damage = 30.0    # done once when shockwave hits a target
        self.wave_damage = 0.1      # done continously while shockwave pushes a target
        self.shock_force_factor = 1.0 # multiplier factor to the shock force, which is the force that pushes/pulls entities from the wave

    def SetRadius(self, r):
        self.radius = r
        self.geometry.set_radius(r)
        self.mass = GetMassByRadius(r)
        scale = GetEquivalentValueInRange(r, self.radius_range, self.scale_range)
        for node in self.nodes:
            node.modifier().set_scale( Vector2D(scale, scale) )
        
    def Update(self, dt):
        self.lifetime += dt
        r = GetEquivalentValueInRange(self.lifetime, [0, self.max_lifetime], self.radius_range)
        self.SetRadius(r)
        if self.lifetime > self.max_lifetime:
            #gotta destroy this thing
            self.is_destroyed = True
            #print self, "is ending..."
            
    def HandleCollision(self, target):
        ignore_types = ["GravityWell", "Planet", "Shockwave", "Satellite"]
        if target.type in ignore_types or target.id in self.ignore_ids:
            return 
        
        #print self, "is affecting", target
        v = self.GetPos() - target.GetPos()
        dist = v.Length()
        v = v.Normalize()
        if self.is_antigrav:
            v = v * -1

        #######
        ## shockwave now seems to push more like we wanted
        ## however its still not perfect, try to follow a straight
        ## line, do a wave, go around the map and shoot in the wave
        ## it should stop the projectiles, but they just go through
        #######

        if target.id in self.affected_targets:
            # continuously affecting target...
            wave_speed = ( self.radius_range[1] - self.radius_range[0] ) / self.max_lifetime
            target.TakeDamage(self.wave_damage)
            v = v * (wave_speed/10.0)
            return
        else:
            # hitting target for the first time
            target.TakeDamage(self.shock_damage)
            self.affected_targets.append(target.id)

            current_r_range = [self.radius, self.radius_range[0]]
            current_shockforce_range = [GetGravForce(self.mass, r) for r in current_r_range]
            current_r_range.reverse()
            ShockForce = GetEquivalentValueInRange(dist, current_r_range, current_shockforce_range )

            v_transpost = Vector2D( -v.get_y(), -v.get_x())
            m = v_transpost * target.velocity
            target_velocity = target.velocity - (v_transpost*m)
            target.velocity = target_velocity

            wave_speed = ( self.radius_range[1] - self.radius_range[0] ) / self.max_lifetime
            v = v * (wave_speed/1.02)

        v = v * self.shock_force_factor
        target.ApplyVelocity(v)
