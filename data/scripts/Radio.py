from ugdk.ugdk_audio import AudioManager, Music
from ugdk.ugdk_base import Engine_reference
from ugdk.ugdk_input import InputManager, K_UP, K_DOWN, K_LEFT, K_RIGHT
from random import randint

SOUND_PATH = "sounds/"

class Radio:
    def __init__(self):
        self.path = "musics/"
        self.sound_path = SOUND_PATH
        self.playlist = ["action_game_theme.ogg", "Arabesque.ogg", "running_from_something.ogg"]
        self.current = self.GetMusicByIndex( randint(0, len(self.playlist)-1) )
        self.index = 0

    def CheckCommands(self):
        input = Engine_reference().input_manager()
        if input.KeyPressed(K_UP):
            self.Play()
        if input.KeyPressed(K_DOWN):
            self.current.Pause()
        if input.KeyPressed(K_RIGHT):
            self.Previous()
        if input.KeyPressed(K_LEFT):
            self.Next()

    def Play(self):
        self.current.PlayForever()

    def GetMusicByIndex(self, i):
        return Engine_reference().audio_manager().LoadMusic(self.path + self.playlist[i] )

    def Next(self):
        self.index += 1
        if self.index >= len(self.playlist):
            self.index = 0
        self.current.Stop()
        self.current = self.GetMusicByIndex(self.index)
        self.current.PlayForever()
    def Previous(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.playlist) - 1
        self.current.Stop()
        self.current = self.GetMusicByIndex(self.index)
        self.current.PlayForever()

    def PlaySound(self, sound_name):
        sound = Engine_reference().audio_manager().LoadSample(self.sound_path + sound_name)
        sound.Play()
