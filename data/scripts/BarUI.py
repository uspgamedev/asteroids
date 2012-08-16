from ugdk.ugdk_graphic import Node, Modifier, Drawable
from ugdk.ugdk_drawable import SolidRectangle
from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Color, Engine_reference

from math import pi

BAR_SIZE = 4.0

class BarUI:
    def __init__(self, entity, attr_name, color, offset, vertical = False):
        self.entity = entity
        self.attr_name = attr_name
        if not hasattr(entity, attr_name):
            print "WARNING! BarUI can't find attribute %s in entity %s" % (attr_name, entity)
        if not hasattr(entity, "max_"+attr_name):
            print "WARNING! BarUI can't find attribute %s in entity %s" % ("max_"+attr_name, entity)

        if vertical:
            self.offset = Vector2D(offset + BAR_SIZE, 0.0)
        else:
            self.offset = Vector2D(0.0, offset + BAR_SIZE)

        self.node = Node()
        self.node.modifier().set_offset( self.offset )
        if vertical:
            self.node.modifier().set_rotation( pi/2.0)
        self.node.thisown = 0

        self.size = Vector2D(entity.size.get_x(), BAR_SIZE)

        self.back_shape = SolidRectangle( self.size )
        self.back_shape.set_color( Color(0.0, 0.0, 0.0, 0.5) )
        self.back_shape.set_hotspot(Drawable.CENTER)
        self.back_node = Node( self.back_shape )
        self.node.AddChild(self.back_node)

        self.shape = SolidRectangle( self.size )
        self.shape.set_color( color )
        self.shape.set_hotspot(Drawable.CENTER)
        self.bar_node = Node( self.shape )
        self.node.AddChild(self.bar_node)

        self.type = str(self.__class__)

    def Update(self):
        if hasattr(self.entity, self.attr_name) and hasattr(self.entity, "max_"+self.attr_name):
            current = self.entity.__dict__[self.attr_name]
            max = self.entity.__dict__["max_"+self.attr_name]
            if current <= 0:    current = 0
            #size = current * self.entity.size.get_x() / max
            #scale = size / self.entity.size.get_x()  # I know this is redundant, by I prefer it in this case to be more verbose

            scale = current / max  #this is same as the commented above, but without the redundancy

            self.bar_node.modifier().set_scale( Vector2D(scale, 1.0) )

    def __repr__(self):
        return "<%s of entity %s>" % (self.type, self.entity)
        
    def __str__(self): return self.__repr__()


class StatsUI:
    def __init__(self, managerScene, x, y, stringFunctions, backColor, backAlpha=1.0):
        self.managerScene = managerScene
        self.node = Node()
        #self.node.thisown = 0
        self.size = Vector2D(150.0, 75.0)
        self.backShape = SolidRectangle( self.size )
        self.backShape.set_color( backColor )
        self.backNode = Node()
        self.backNode.set_drawable( self.backShape )
        color = self.backNode.modifier().color()
        color.set_a(backAlpha)
        self.backNode.modifier().set_color(color)
        self.node.AddChild(self.backNode)
        self.node.modifier().set_offset( Vector2D(x,y) )
        
        self.texts = []
        self.stringsFunctions = stringFunctions
        self.strings = [f() for f in self.stringsFunctions]
        y = 0
        for i in range(len(self.strings)):
            self.texts.append( Engine_reference().text_manager().GetText(self.strings[i]) )
            textNode = Node()
            textNode.set_drawable(self.texts[i])
            textNode.modifier().set_offset( Vector2D(0.0, i * 20.0 ) )
            #textNode.thisown = 0
            self.node.AddChild(textNode)
            if self.texts[i].size().get_x() > self.size.get_x():
                self.size.set_x(self.texts[i].size().get_x())
            y += self.texts[i].size().get_y() + 5
        self.size.set_y(y)
        self.backShape.set_size(self.size)

    def SetPos(self, x, y):
        self.node.modifier().set_offset(Vector2D(x,y))

    def UpdateSize(self, w, h):
        self.size.set_x(w)
        self.size.set_y(h)
        self.backShape.set_size(self.size)
        screenSize = Engine_reference().video_manager().video_size()
        x = self.node.modifier().offset().get_x()
        y = self.node.modifier().offset().get_y()
        if x + w > screenSize.get_x():
            x = screenSize.get_x() - w
        if y + h > screenSize.get_y():
            y = screenSize.get_y() - h
        if x < 0:   x = 0
        if y < 0:   y = 0
        self.SetPos(x,y)

    def Update(self):
        w = self.size.get_x()
        h = 0
        update_size = False
        for i in range(len(self.stringsFunctions)):
            newstr = self.stringsFunctions[i]()
            if newstr != self.strings[i]:
                self.strings[i] = newstr
                self.texts[i].SetMessage(newstr)
                if self.texts[i].size().get_x() > w:
                    w = self.texts[i].size().get_x()
                update_size = True
            h += self.texts[i].size().get_y() + 5

        if update_size: self.UpdateSize(w,h)
