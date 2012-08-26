from ugdk.ugdk_math import Vector2D
from ugdk.ugdk_base import Engine_reference, ResourceManager_GetTextureFromFile
from ugdk.ugdk_graphic import Node
from ugdk.ugdk_drawable import TexturedRectangle
from Ship import Ship
from Asteroid import Asteroid
from Planet import Planet
import random
from math import pi
import Config

PERCENT_OF_ENTITIES_IN_MAP_GRID = 0.3

ASTEROID_STARTING_SPEED_RANGE = [40, 110]

PLANET_COUNT_RANGE = [0, 2]

def GetCellCenter(i, j):
    x = j * Config.MAX_ENTITY_SIZE + (Config.MAX_ENTITY_SIZE/2.0)
    y = i * Config.MAX_ENTITY_SIZE + (Config.MAX_ENTITY_SIZE/2.0)
    return (x, y)

def RandInRange(start, end):
    return random.random()*(end-start) + start
    
def GetRandomAsteroidSizeFactor(difficultyFactor):
    # returns random float in [0.5, 1.2[
    if difficultyFactor < 1.0:
        return RandInRange(0.4, 1.0)
    elif difficultyFactor < 5.0:
        return RandInRange(0.8, 1.6)
    elif difficultyFactor < 15.0:
        return RandInRange(1.5, 3.0)
    elif difficultyFactor < 50.0:
        return RandInRange(2.0, 4.0)
    else:
        return RandInRange(4.0, 10.0)
    
def GetRandomPlanetSizeFactor():
    # returns random float in [0.7, 1.5[
    return RandInRange(0.7, 1.5)

def Generate(difficultyFactor, heroData):
    screenSize = Config.gamesize
    print "Screen Size = (%s, %s)" % (screenSize.get_x(), screenSize.get_y())
    
    entities = []
    # for the purpose of generating random map objects, we create a imaginary table henceforth known as the "MAP"
    # the MAP represents the playable area (from now on, no longer related to the screen).
    # each cell in the map is of the size MAX_ENTITY_SIZExMAX_ENTITY_SIZE
    # a object can only be placed in the center position of a cell, and only one object per cell,
    # although there can be empty cells.
    #
    # this way we have a simple way of knowing where we can place objects, with the benefit that
    # at least in theory, they should not be colliding with each other
    rows = int( screenSize.get_y() / Config.MAX_ENTITY_SIZE )
    columns = int( screenSize.get_x() / Config.MAX_ENTITY_SIZE )

    # WHAT SORCERY IS THIS?!?
    map_row = [False] * columns
    map = [map_row] * rows

    n = int( (rows * columns) * PERCENT_OF_ENTITIES_IN_MAP_GRID )

    print "Generating a %sx%s map with %s entities..." % (rows, columns, n)

    possibleCells = [(i,j) for i in range(rows) for j in range(columns)]
    random.shuffle(possibleCells)
    # I had so many awesome ideas using awesome python features to do this 
    # (generate a list of all possible cell (x, y) locations)

    def pickAPlace(removeAdjacents=False):
        if len(possibleCells) == 0: return (random.random()*600, random.random()*400)
        i, j = possibleCells.pop()
        if removeAdjacents:
            neighbours = [(i+offi,j+offj) for offi in range(-1,2) for offj in range(-1,2) if not (offi,offj) == (0,0)]
            while len(neighbours) > 0:
                adjacent = neighbours.pop()
                if adjacent in possibleCells:   
                    possibleCells.remove(adjacent)
                    map[adjacent[0]][adjacent[1]] = True
        map[i][j] = True
        return GetCellCenter(i, j)
    ##

    if heroData != None:
        loc = pickAPlace(True) #remove adjacent places so that the player starts with a little room
        ship = Ship(loc[0], loc[1], heroData)
        entities.append(ship)

    planetCount = int( random.randint(PLANET_COUNT_RANGE[0], PLANET_COUNT_RANGE[1])   )
    for i in range(planetCount):
        loc = pickAPlace()
        planet = Planet(loc[0], loc[1], GetRandomPlanetSizeFactor())
        entities.append(planet)

    for i in range(n):
        loc = pickAPlace()
        ast = Asteroid(loc[0], loc[1], GetRandomAsteroidSizeFactor(difficultyFactor))
        v = Vector2D(1,0).Rotate( random.random() * 2 * pi )
        v = v.Normalize()
        v = v * (random.randint(ASTEROID_STARTING_SPEED_RANGE[0], ASTEROID_STARTING_SPEED_RANGE[1]))
        ast.ApplyVelocity(v)
        entities.append(ast)

    return entities


def GetBackgroundDrawable():
    screenSize = Config.gamesize #Engine_reference().video_manager().video_size()
    texture_obj = ResourceManager_GetTextureFromFile("images/background%s.jpg" % (random.randint(1,3)))
    background = TexturedRectangle( texture_obj, screenSize )
    background.thisown = 0
    return background
