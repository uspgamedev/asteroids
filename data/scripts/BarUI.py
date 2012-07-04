from ugdk.ugdk_graphic import Node, Modifier, Drawable
from ugdk.ugdk_drawable import SolidRectangle
from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Color, Engine_reference

BAR_HEIGHT = 4.0

class BarUI:
    def __init__(self, entity, attr_name, color, offset):
        self.entity = entity
        self.attr_name = attr_name
        if not hasattr(entity, attr_name):
            print "WARNING! BarUI can't find attribute %s in entity %s" % (attr_name, entity)
        if not hasattr(entity, "max_"+attr_name):
            print "WARNING! BarUI can't find attribute %s in entity %s" % ("max_"+attr_name, entity)
        self.offset = offset
        self.offset.set_y( offset.get_y() + BAR_HEIGHT)

        self.node = Node()
        self.node.modifier().set_offset( self.offset )
        self.node.thisown = 0

        self.nodes = []
        for i in range(2):
            for j in range(2):
                import Config

                node = Node()
                node.modifier().set_offset(Vector2D(Config.gamesize.get_x() * i, Config.gamesize.get_y() * j))
                self.node.AddChild(node)
                self.nodes.append(node)

        self.back_shapes = []
        self.back_nodes = []
        self.shapes = []
        self.bar_nodes = []
        for node in self.nodes:
            back_shape = SolidRectangle( Vector2D(entity.size.get_x(), BAR_HEIGHT) )
            back_shape.set_color( Color(0.0, 0.0, 0.0, 0.5) )
            back_shape.set_hotspot(Drawable.CENTER)
            back_node = Node( back_shape )
            node.AddChild(back_node)
            self.back_shapes.append(back_shape)
            self.back_nodes.append(back_node)

            shape = SolidRectangle( Vector2D(entity.size.get_x(), BAR_HEIGHT) )
            shape.set_color( color )
            shape.set_hotspot(Drawable.CENTER)
            bar_node = Node( shape )
            node.AddChild(bar_node)
            self.shapes.append(shape)
            self.bar_nodes.append(bar_node)

        self.type = str(self.__class__)

    def Update(self):
        if hasattr(self.entity, self.attr_name) and hasattr(self.entity, "max_"+self.attr_name):
            current = self.entity.__dict__[self.attr_name]
            max = self.entity.__dict__["max_"+self.attr_name]
            if current <= 0:    current = 0
            size = current * self.entity.size.get_x() / max
            scale = size / self.entity.size.get_x()  # I know this is redundant, by I prefer it in this case to be more verbose
            for bar_node in self.bar_nodes:
                bar_node.modifier().set_scale( Vector2D(scale, 1.0) )

    def __repr__(self):
        return "<%s of entity %s>" % (self.type, self.entity)
        
    def __str__(self): return self.__repr__()


class StatsUI:
    def __init__(self, managerScene, x, y, backColor, backAlpha=1.0):
        self.managerScene = managerScene
        self.node = Node()
        #self.node.thisown = 0
        self.backShape = SolidRectangle( Vector2D(150.0, 75.0) )
        self.backShape.set_color( backColor )
        self.node.set_drawable( self.backShape )
        self.node.modifier().set_alpha(backAlpha)
        self.node.modifier().set_offset( Vector2D(x,y) )
        
        self.texts = []
        self.stringsFunctions = [self.GetLivesText, self.GetDifficultyText,
                                    self.GetPointsText, self.GetShipPosition, self.GetShipHudPosition]
        self.strings = [f() for f in self.stringsFunctions]
        for i in range(len(self.strings)):
            self.texts.append( Engine_reference().text_manager().GetText(self.strings[i]) )
            textNode = Node()
            textNode.set_drawable(self.texts[i])
            textNode.modifier().set_offset( Vector2D(0.0, i * 20.0 ) )
            #textNode.thisown = 0
            self.node.AddChild(textNode)

    def GetLivesText(self):
        return "Lives: %s" % (self.managerScene.lives)

    def GetDifficultyText(self):
        return "Difficulty: %.2f" % (self.managerScene.difficulty)

    def GetPointsText(self):
        return "Points: %d" % (self.managerScene.points)

    def GetShipPosition(self):
        try:
            pos = Engine_reference().CurrentScene().GetHero().GetPos()
            return "Ship Position: %.1f; %.1f" % (pos.get_x(), pos.get_y())
        except:
            return ""
    
    def GetShipHudPosition(self):
        try:
            pos = Engine_reference().CurrentScene().GetHero().hud_node.modifier().offset()
            return "Ship Hud Position: %.1f; %.1f" % (pos.get_x(), pos.get_y())
        except:
            return ""

    def Update(self):
        for i in range(len(self.stringsFunctions)):
            newstr = self.stringsFunctions[i]()
            if newstr != self.strings[i]:
                self.strings[i] = newstr
                self.texts[i].SetMessage(newstr)
            
