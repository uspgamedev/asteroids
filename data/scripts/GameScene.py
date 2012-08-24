from ugdk.ugdk_action import Scene, Task
from ugdk.ugdk_util import CreateBox2D
from ugdk.pyramidworks_collision import CollisionManager, CollisionInstanceList
from ugdk.ugdk_input import InputManager, K_ESCAPE, K_HOME, K_END, K_PAGEUP, K_PAGEDOWN, K_p, K_SPACE, K_1, K_2, K_3, K_4, K_5
from ugdk.ugdk_base import Engine_reference, ResourceManager_CreateTextFromLanguageTag, Color
from ugdk.ugdk_drawable import SolidRectangle
from ugdk.ugdk_graphic import Node
from ugdk.ugdk_math import Vector2D
from Radio import Radio, SOUND_PATH
import Config
import MapGenerator
import BarUI
import Ship
    

import ItemFactory

def StartupScene():
    #print "STARTING SCENE"
    cena = ManagerScene()
    #print "GOING TO PUSH SCENE"
    Engine_reference().PushScene( cena )
    return cena


class ManagerScene (Scene):
    IDLE = 0
    ACTIVE = 1
    PLAYER_DIED = 2
    PLAYER_WON = 3
    PLAYER_QUIT = 4
    def __init__(self):
        self.lives = 5
        self.difficulty = 0.5
        self.points = 0
        self.status = ManagerScene.IDLE
        self.heroData = Ship.ShipData(100.0, 100.0, 25.0, 1, 0.0)
        strFuncs = [self.GetLivesText, self.GetDifficultyText, self.GetPointsText]
        self.stats = BarUI.StatsUI(self, 100.0, 100.0, strFuncs, Color(0.6,0.6,0.6), 0.4)
        self.interface_node().AddChild(self.stats.node)
        self.radio = Radio()
        self.hero_effects = []

    def GetLivesText(self):
        return "Lives: %s" % (self.lives)

    def GetDifficultyText(self):
        return "Difficulty: %.2f" % (self.difficulty)

    def GetPointsText(self):
        return "Points: %d" % (self.points)

    def Focus(self):
        self.stats.node.set_active(True)

    def DeFocus(self):
        self.stats.node.set_active(False)

    def Update(self, dt):  ###
        self.CheckCommands()
        self.radio.CheckCommands()
        self.stats.Update()
        if self.status == ManagerScene.PLAYER_QUIT:
            self.Finish()
            return
        replay = self.status != ManagerScene.ACTIVE
        if replay and self.lives > 0:
            if self.status == ManagerScene.PLAYER_WON:
                if self.difficulty < 1.0:   self.difficulty += 0.25
                elif self.difficulty < 3.0:   self.difficulty += 0.5
                elif self.difficulty < 15.0:    self.difficulty += 1.0
                else:   self.difficulty += 5.0
                print "Game WON!"
            elif self.status == ManagerScene.PLAYER_DIED:
                print "You are no match for teh might of teh Asteroid Army!"
            
            cena = AsteroidsScene(self, self.difficulty)
            Engine_reference().PushScene(cena)
            cena.GenerateMap(self.heroData)
            for e_func, e_attrDict in self.hero_effects:
                e = e_func()
                e.SetTarget(cena.hero)
                e.creation_func = e_func
                for key, value in e_attrDict.items():
                    e.__dict__[key] = value
                cena.hero.ApplyEffect(e)
            self.hero_effects = []
            self.status = ManagerScene.ACTIVE
            #print "=== Starting Asteroids Scene [Difficulty = %s][Lives Left = %s][%s]" % (self.difficulty, self.lives, self.heroData)
            
    def UpdateLives(self, amount): self.lives += amount
    def UpdatePoints(self, amount): self.points += amount

    def SetGameResult(self, won, hero_effects):
        if won:
            self.status = ManagerScene.PLAYER_WON
        else:
            self.status = ManagerScene.PLAYER_DIED
            self.UpdateLives(-1)
        self.hero_effects = hero_effects

    def SetGameQuit(self):
        self.status = ManagerScene.PLAYER_QUIT

    def CheckCommands(self):
        input = Engine_reference().input_manager()
        
        if input.KeyPressed(K_ESCAPE):
            print "Manager ESCAPING"
            self.Finish()

    def End(self):
        pass

class SceneFinishTask(Task):
    def __init__(self, delay):
        self.timeRemaining = delay

    def __call__(self, dt):
        self.timeRemaining -= dt
        if self.timeRemaining <= 0:
            Engine_reference().CurrentScene().Finish()
            return False
        return True


class AsteroidsScene (Scene):
    def __init__(self, managerScene, difficultyFactor):
        #print "Creating AsteroidsScene"
        maxval = Config.MAX_ENTITY_SIZE
        mincoords = [-maxval, -maxval]
        maxcoords = [Config.gamesize.get_x() + maxval,  Config.gamesize.get_y() + maxval]
        self.collisionManager = CollisionManager( CreateBox2D(mincoords[0], mincoords[1], maxcoords[0], maxcoords[1]) )
        self.objects = []
        self.colliding_objects = []
        self.startCollisions()
        self.asteroid_count = 0
        self.ship_alive = True
        self.hero = None
        self.hero_effects = []
        self.finishTextNode = None
        self.difficultyFactor = difficultyFactor
        #self.AddTask(self.collisionManager.GenerateHandleCollisionTask() )###
        self.managerScene = managerScene
        strFuncs = [self.managerScene.GetLivesText, self.managerScene.GetDifficultyText, self.managerScene.GetPointsText]
        self.stats = BarUI.StatsUI(managerScene, 0.0, 0.0, strFuncs, Color(0.0,0.0,0.0), 0.4)
        heroFuncs = [self.HeroPulseStats, self.HeroWeaponStats, self.HeroLifeStats, self.HeroEnergyStats, self.HeroLifeRegen, self.HeroEnergyRegen]
        self.hero_stats = BarUI.StatsUI(managerScene, Config.resolution.get_x()-150.0, 0.0, heroFuncs, Color(0.0,0.0,0.0), 0.4)
        self.hud = Node()
        self.interface_node().AddChild(self.hud)
        
    def HeroPulseStats(self):
        if self.hero != None and not self.hero.is_destroyed:
            return " Pulse: %s x %s : %s " % (self.hero.data.pulse_damage, self.hero.data.pulse_shots, self.hero.data.homing)
        return ""

    def HeroWeaponStats(self):
        if self.hero != None and not self.hero.is_destroyed:
            if self.hero.right_weapon != None:
                return " Weapon: %s " % (self.hero.right_weapon.type)
            else:
                return " Weapon: None "
        return ""

    def HeroLifeStats(self):
        if self.hero != None and not self.hero.is_destroyed:
            return " Life: %2.2f/%s " % (self.hero.life, self.hero.max_life)
        return ""

    def HeroEnergyStats(self):
        if self.hero != None and not self.hero.is_destroyed:
            return " Energy: %2.2f/%s " % (self.hero.energy, self.hero.max_energy)
        return ""

    def HeroLifeRegen(self):
        if self.hero != None and not self.hero.is_destroyed:
            aedl = self.hero.GetActiveEffectsDetailsList()
            for s in aedl:
                if s.count("Life Regen"):
                    return " "+s+" "
        return ""

    def HeroEnergyRegen(self):
        if self.hero != None and not self.hero.is_destroyed:
            aedl = self.hero.GetActiveEffectsDetailsList()
            for s in aedl:
                if s.count("Energy Regen"):
                    return " "+s+" "
        return ""

    def startCollisions(self):
        self.collisionManager.Generate("Entity")
        self.collisionManager.Generate("Gravity")
        self.collisionManager.Generate("PowerUp")
        self.collisionManager.Generate("RangeCheck")
        self.collisionManager.Generate("Beam")

    def GetHero(self):  return self.hero

    def Populate(self, objs):
        #print self, " POPULATE: receiving objects ", objs
        for obj in objs:
            self.AddObject(obj)
            
    def AddObject(self, obj):
        self.objects.append(obj)
        if obj.is_collidable:
            self.colliding_objects.append(obj)
            obj.collision_object.StartColliding()
        self.AddEntity(obj)
        #print self, "GOING TO ADD OBJECT %s [node=%s]" % (obj, obj.node)
        if obj.GetNode() != None:
            CN = self.content_node()
            CN.AddChild(obj.GetNode())
        #print "SCENE CONTENT NODE = ", CN
        if obj.GetHUDNode():
            self.hud.AddChild(obj.hud_node)
        #print "FINISHED ADDING OBJECT"
        if obj.CheckType("Asteroid"):
            self.asteroid_count += 1
        if obj.CheckType("Ship"):
            self.ship_alive = True
            self.hero = obj
            
    def RemoveObject(self, obj):
        if obj.CheckType("Asteroid"):
            self.asteroid_count -= 1
        if obj.CheckType("Ship"):
            self.ship_alive = False
            self.managerScene.heroData = self.hero.data
            if self.hero.right_weapon != None:
                self.hero_effects = [self.hero.right_weapon.GetCreationFunc()]
            self.hero = None
        self.managerScene.UpdatePoints( obj.GetPointsValue() )
        self.objects.remove(obj)
        if obj in self.colliding_objects:
            self.colliding_objects.remove(obj)
        self.RemoveEntity(obj)
        obj.to_be_removed = True
        #print "REMOVING OBJECT %s [%s]" % (obj, obj.node)
        if obj.collision_object != None:
            obj.collision_object.StopColliding()
        obj.node.thisown = 1
        del obj.node
        obj.hud_node.thisown = 1
        del obj.hud_node
        del obj
        
        
    def GenerateMap(self, heroData):
        #print "GENERATE MARK 1"
        self.Populate( MapGenerator.Generate(self.difficultyFactor, heroData) )
        #print "GENERATE MARK 2"
        self.content_node().set_drawable(MapGenerator.GetBackgroundDrawable() )
        #print "GENERATE MARK 3"
        self.interface_node().AddChild(self.stats.node)
        self.interface_node().AddChild(self.hero_stats.node)

    def ReGenerateMap(self, df, heroData):
        self.difficultyFactor = df
        # remove old objects
        to_delete = [obj for obj in self.objects if not obj.CheckType("Ship")]
        for obj in to_delete:
            self.RemoveObject(obj)

        self.finishTextNode.thisown = 1
        del self.finishTextNode
        self.finishTextNode = None
        # populate the map
        data = None
        if self.hero == None:   data = heroData
        self.Populate( MapGenerator.Generate(self.difficultyFactor, data) )
        self.content_node().set_drawable(MapGenerator.GetBackgroundDrawable() )
        
    def GetLivePlanetsPoints(self):
        v = 0
        for obj in self.objects:
            if obj.CheckType("Planet") and not obj.is_destroyed:
                v += obj.life
        return v

    def SetAndShowSceneEndText(self, msgTag):
        if self.finishTextNode != None: return
        text = ResourceManager_CreateTextFromLanguageTag(msgTag)
        self.finishTextNode = Node(text)
        screenSize = Engine_reference().video_manager().video_size()
        x = (screenSize.get_x()/2.0) - (text.width()/2.0)
        y = (screenSize.get_y()/2.0) - (text.height()/2.0)
        self.finishTextNode.modifier().set_offset( Vector2D(x, y) )
        self.interface_node().AddChild(self.finishTextNode)

    def CheckForEndGame(self):
        if self.finishTextNode != None: return
        if self.asteroid_count <= 0:
            if self.hero.right_weapon != None:
                self.hero_effects = [self.hero.right_weapon.GetCreationFunc()]
            self.hero_effects = self.hero_effects + [e.GetCreationFunc() for e in self.hero.GetActiveEffectsList()]
            self.SetAndShowSceneEndText("GameWon")
            self.managerScene.SetGameResult(True, self.hero_effects)
            self.managerScene.UpdatePoints( self.GetLivePlanetsPoints() * self.managerScene.difficulty )
            phl = 100
            if self.hero != None:
                phl = self.hero.life * 5
            self.managerScene.UpdatePoints( phl )
            self.AddTask(SceneFinishTask(5.0))
        elif not self.ship_alive:
            self.SetAndShowSceneEndText("GameOver")
            self.managerScene.SetGameResult(False, self.hero_effects)
            self.AddTask(SceneFinishTask(5.0))
        
    def Focus(self):
        self.managerScene.radio.Play()

    def DeFocus(self):
        pass

    def Update(self, dt):  ###   
        to_delete = [o for o in self.objects if o.is_destroyed]
        for obj in to_delete:
            self.RemoveObject(obj)
            
        self.CheckForEndGame()
        self.stats.Update()
        self.hero_stats.Update()
        self.CheckCommands()
        self.managerScene.radio.CheckCommands()
        self.HandleCollisions()###
        
        #if self.hero != None:
        #    offset = self.hero.GetPos()
        #    self.content_node().modifier().set_offset(offset)
            #self.interface_node().modifier().set_offset(offset)
        
    def CheckCommands(self):
        input = Engine_reference().input_manager()
        
        if input.KeyPressed(K_ESCAPE):
            print "GameScene ESCAPING"
            self.managerScene.SetGameQuit()
            self.Finish()
        elif input.KeyPressed(K_SPACE) or input.KeyPressed(K_p):
            Engine_reference().PushScene( PauseScene() )
        ### cheats
        elif input.KeyPressed(K_PAGEUP):
            self.managerScene.difficulty += 1
        elif input.KeyPressed(K_PAGEDOWN):
            self.managerScene.difficulty -= 1
        elif input.KeyPressed(K_HOME):
            self.managerScene.lives += 1
        elif input.KeyPressed(K_END):
            self.hero.invulnerable = True
        elif input.KeyPressed(K_1):
            cheat = ItemFactory.CreateRepairPack(self.hero.GetPos().get_x(), self.hero.GetPos().get_y())
            self.AddObject(cheat)
        elif input.KeyPressed(K_2):
            cheat = ItemFactory.CreatePulsePack(self.hero.GetPos().get_x(), self.hero.GetPos().get_y())
            self.AddObject(cheat)
        elif input.KeyPressed(K_3):
            cheat = ItemFactory.CreatePassivePack(self.hero.GetPos().get_x(), self.hero.GetPos().get_y())
            self.AddObject(cheat)
        elif input.KeyPressed(K_4):
            cheat = ItemFactory.CreateActivePack(self.hero.GetPos().get_x(), self.hero.GetPos().get_y())
            self.AddObject(cheat)
        elif input.KeyPressed(K_5):
            cheat = ItemFactory.CreateInstantPack(self.hero.GetPos().get_x(), self.hero.GetPos().get_y())
            self.AddObject(cheat)
            
    def HandleCollisions(self):
        collision_list = CollisionInstanceList()
        #print "HandleCollisions COLLISION_LIST = ", collision_list
        for obj in self.colliding_objects:
            if not obj.is_destroyed:
                obj.collision_object.SearchCollisions(collision_list)
            
        for col in collision_list:
            #print "HC", col
            #print "HANDLE COLLISION::  [%s].Handle(%s)" % (col[0], col[1])
            col[0].Handle(col[1])
            
            
    def End(self):
        if self.hero != None:
            self.managerScene.heroData = self.hero.data

################################################################################

class PauseScene (Scene):
    def __init__(self):
        screenSize = Engine_reference().video_manager().video_size()
        rect = SolidRectangle(screenSize)
        rect.set_color( Color(0.5, 0.5, 0.5) )
        self.backNode = Node(rect)
        color = self.backNode.modifier().color()
        color.set_a(0.5)
        self.backNode.modifier().set_color(color)
        self.content_node().AddChild(self.backNode)

        text = ResourceManager_CreateTextFromLanguageTag("Pause")
        self.textNode = Node(text)
        x = (screenSize.get_x()/2.0) - (text.width()/2.0)
        y = (screenSize.get_y()/2.0) - (text.height()/2.0)
        self.textNode.modifier().set_offset( Vector2D(x, y) )
        self.interface_node().AddChild(self.textNode)

    def Focus(self):
        pass

    def DeFocus(self):
        pass

    def Update(self, dt):  ###
        input = Engine_reference().input_manager()
        resume = False
        resume = resume or input.KeyPressed(K_ESCAPE)
        resume = resume or input.KeyPressed(K_HOME)
        resume = resume or input.KeyPressed(K_PAGEUP)
        resume = resume or input.KeyPressed(K_PAGEDOWN)
        resume = resume or input.KeyPressed(K_p)
        resume = resume or input.KeyPressed(K_SPACE)
        if resume:
            self.Finish()

            
    def End(self):
        pass
