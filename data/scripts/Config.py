from ugdk.ugdk_math import Vector2D

#################################
# Game Settings
#################################
# Video Config
resolution = Vector2D(1024.0, 768.0)
fullscreen = False

# Language Config
language = "en_US"


##################################
# Game Parameters
##################################

gamesize = resolution#Vector2D(2000.0, 2000.0)
MAX_ENTITY_SIZE = 200.0


# PowerUps
baseDropRate = 0.2      # base chance to a factor 1 asteroid to drop a item when breaking.

repairChance = 30.0     # the <powerUpType>Chance variables should sum up to 100.0
pulseChance = 10.0
passiveChance = 20.0
activeChance = 20.0
instantChance = 20.0
