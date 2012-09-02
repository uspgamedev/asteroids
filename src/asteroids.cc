
#include <cerrno>
#include <sys/stat.h>

#include <string>
#include <list>

#include "SDL.h"

#include <ugdk/base/engine.h>
#include <ugdk/base/configuration.h>
#include <ugdk/graphic/videomanager.h>
#include <ugdk/graphic/textmanager.h>
#include <ugdk/math/vector2D.h>
#include <ugdk/util/languagemanager.h>
#include <ugdk/modules.h>
#include <pyramidworks/modules.h>

#include <ugdk/script/scriptmanager.h>
#include <ugdk/script/langwrapper.h>
#include <ugdk/script/virtualobj.h>
#include <ugdk/script/languages/python/pythonwrapper.h>

#include "config.h"

using ugdk::Vector2D;
using ugdk::script::VirtualObj;

/////////////////////////////////////////////////////////////////

static void InitScripts() {
    using ugdk::script::lua::LuaWrapper;
    using ugdk::script::python::PythonWrapper;

    //inicializando python
    PythonWrapper* py_wrapper = new PythonWrapper();
    ugdk::RegisterPythonModules(py_wrapper);
    pyramidworks::RegisterPythonModules(py_wrapper);
    SCRIPT_MANAGER()->Register("Python", py_wrapper);
}

int main(int argc, char *argv[]) {

    ugdk::Configuration engine_config;
#ifdef DEBUG
    engine_config.window_title = "Asteroids DEBUG";
#else
    engine_config.window_title = "Asteroids";
#endif
    engine_config.window_size  = Vector2D(640.0, 480.0);
    engine_config.fullscreen   = false;
    engine_config.base_path = ASTEROIDS_DATA_PATH;
	engine_config.window_icon = "asteroids_wars.bmp";
    struct stat st;
    // Removing the trailing slash.
    int s = stat(engine_config.base_path.substr(0, engine_config.base_path.size() - 1).c_str(), &st);
    if(s < 0 && errno == ENOENT)
        engine_config.base_path = "./data/";

    InitScripts();
    ugdk::Engine::reference()->Initialize(engine_config);

    VirtualObj config = SCRIPT_MANAGER()->LoadModule("Config");

    Vector2D* resolution = config["resolution"].value<Vector2D*>();
    VIDEO_MANAGER()->ChangeResolution(*resolution, config["fullscreen"].value<bool>());
    VIDEO_MANAGER()->SetVSync(true);

    VirtualObj languages = SCRIPT_MANAGER()->LoadModule("Languages");
    languages["RegisterLanguages"]();
    if(!ugdk::Engine::reference()->language_manager()->Setup( config["language"].value<std::string>() )) {
        fprintf(stderr, "Language Setup FAILURE!!\n\n");
    }

    VirtualObj scene_script = SCRIPT_MANAGER()->LoadModule("GameScene");
    {
        VirtualObj first_scene = scene_script["StartupScene"]();
        //if this object, which is scene, exists when main ends, and that same scene
        //was already deleted segfault occured
    }
    
    // Transfers control to the framework.
    ugdk::Engine::reference()->Run();

    // Releases all loaded textures, to avoid issues when changing resolution.
    ugdk::Engine::reference()->video_manager()->Release();
    ugdk::Engine::reference()->text_manager()->Release();

    ugdk::Engine::reference()->Release();

    return 0;
}
