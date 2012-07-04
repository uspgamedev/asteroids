
CMAKE_MINIMUM_REQUIRED(VERSION 2.6)
PROJECT(asteroids CXX C)
SET(GAME_EXENAME asteroids)
SET(GAME_NAME "Asteroids")
SET(GAME_VERSION "1.0.0 Alpha")
SET(CMAKE_BUILD_TYPE Release)

# Arquivos de codigo fonte vao aqui!
SET(GAME_SRCS 
    ./src/asteroids.cc 
)

IF (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    SET(GAME_SRCS ${GAME_SRCS} src/mac/SDLMain.h src/mac/SDLMain.m)
ENDIF ()

MESSAGE("${GAME_NAME} version ${GAME_VERSION}")

IF (UNIVERSAL)
  # Necessary for a Mac Universal Binary
  SET (CMAKE_OSX_ARCHITECTURES ppc;i386;x86_64)
  SET (CMAKE_OSX_SYSROOT /Developer/SDKs/MacOSX10.5.sdk)
  SET (MACOSX_DEPLOYMENT_TARGET 10.5)
ENDIF (UNIVERSAL)

# #define's que voce queira incluir na compilacao
# separe por espacos
SET(DEFS "" CACHE STRING "#define's que voce queira incluir na compilacao; separe por espacos")
IF(WIN32)
  SET(DEFS "${DEFS} WIN32")
ENDIF(WIN32)

# CFLAGS: flags que voce queira enviar ao compilador
# LDFLAGS: flags que voce queira enviar ao ligador
SET(CFLAGS "" CACHE STRING "flags enviadas ao compilador")
SET(LDFLAGS "" CACHE STRING "flags enviadas ao linker")
IF(UNIX)
  # se for o g++ para *nix:
  SET(CFLAGS "${CFLAGS} -g -Wall -ansi -O3 -U_FORTIFY_SOURCE -msse2")
  IF(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    IF(UNIVERSAL)
      SET(LDFLAGS "${LDFLAGS} -mmacosx-version-min=10.5")
    ELSE()
      SET(LDFLAGS "${LDFLAGS}")
    ENDIF()
  ELSE()
    SET(LDFLAGS "${LDFLAGS}")
  ENDIF()
ELSE(UNIX)
  IF(MINGW)
    # se for o g++ para Windows:
    SET(CFLAGS "${CFLAGS} -Wall -ansi -O3 -U_FORTIFY_SOURCE")
    SET(LDFLAGS "${LDFLAGS}")
  ELSE(MINGW)
    # se for o Microsoft Visual C++:
    SET(CFLAGS "${CFLAGS}")
    SET(LDFLAGS "${LDFLAGS}")
  ENDIF(MINGW)
ENDIF(UNIX)

# Encontrando as bibliotecas necessarias:
find_package(OpenGL REQUIRED)
include_directories(${OPENGL_INCLUDE_DIR})

find_package(SDL REQUIRED)
include_directories(${SDL_INCLUDE_DIR})

find_package(SDL_mixer REQUIRED)
include_directories(${SDLMIXER_INCLUDE_DIR})

find_package(SDL_ttf REQUIRED)
include_directories(${SDLTTF_INCLUDE_DIR})

find_package(SDL_image REQUIRED)
include_directories(${SDLIMAGE_INCLUDE_DIR})

find_package(Lua51 REQUIRED)
include_directories(${LUA_INCLUDE_DIR})

find_package(PythonLibs 2.7 REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

find_library (LUGDK ugdk_d lib/)
if (NOT LUGDK)
    find_library (LUGDK ugdk lib/)
    if (NOT LUGDK)
        message (FATAL_ERROR "Fatal error: libugdk not found!")
    endif (NOT LUGDK)
endif (NOT LUGDK)

# pre-processor: #define's
IF(MSVC)
  FOREACH(d ${DEFS})
    SET(CFLAGS_EXTRA "${CFLAGS_EXTRA} /D${d}")
  ENDFOREACH(d)
ELSE(MSVC)
  FOREACH(d ${DEFS})
    SET(CFLAGS_EXTRA "${CFLAGS_EXTRA} -D${d}")
  ENDFOREACH(d)
ENDIF(MSVC)

cmake_policy(SET CMP0015 NEW)
link_directories ("lib")
include_directories ("include")
include_directories ("src")

if (CMAKE_COMPILER_IS_GNUCXX)
	set (EXTRA_LIBRARIES m ${EXTRA_LIBRARIES})
endif (CMAKE_COMPILER_IS_GNUCXX)
if (MINGW)
	set (EXTRA_LIBRARIES mingw32 ${EXTRA_LIBRARIES})
endif (MINGW)
if (WIN32)
	set (EXTRA_LIBRARIES Ws2_32 ${EXTRA_LIBRARIES})
endif (WIN32)

ADD_EXECUTABLE(${GAME_EXENAME} ${GAME_SRCS})
SET_TARGET_PROPERTIES(${GAME_EXENAME} PROPERTIES LINK_FLAGS "${LDFLAGS}")
SET_TARGET_PROPERTIES(${GAME_EXENAME} PROPERTIES COMPILE_FLAGS "${CFLAGS} ${CFLAGS_EXTRA}")
SET_TARGET_PROPERTIES(${GAME_EXENAME} PROPERTIES PROJECT_NAME "${GAME_NAME}")
TARGET_LINK_LIBRARIES (${GAME_EXENAME}
                         ${EXTRA_LIBRARIES}
                         ${LUGDK}
                         ${SDL_LIBRARY}
                         ${SDLMIXER_LIBRARY}
                         ${SDLTTF_LIBRARY}
                         ${SDLIMAGE_LIBRARY}
                         ${OPENGL_LIBRARIES}
                         ${PYTHON_LIBRARIES}
                         ${LUA_LIBRARIES}
                        )


# Installing on *nix
IF(UNIX)
  IF (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    # Mac
    SET(CHECKMAC "#define ISMAC 1")
    SET(GAME_INSTALL_DIR ".")
  ELSE()
    SET(GAME_INSTALL_DIR "/usr/share/${GAME_EXENAME}/data")
    set (GAME_LOCAL_DIR "./data")
    SET(GAME_FINAL_DIR "/usr/bin")
    
    INSTALL(CODE "MESSAGE(\"Installing ${GAME_NAME} ${GAME_VERSION}... Make sure you have root privileges.\")")
    install (CODE
      "set_target_properties (${GAME_EXENAME} PROPERTIES COMPILE_FLAGS) \"${CFLAGS} ${CFLAGS_EXTRA} -DINSTALLED\""
    )
    
    INSTALL(TARGETS ${GAME_EXENAME} RUNTIME DESTINATION ${GAME_INSTALL_DIR})
    #INSTALL(FILES license.txt readme.html DESTINATION ${GAME_INSTALL_DIR})
    INSTALL(DIRECTORY data DESTINATION ${GAME_INSTALL_DIR})

    INSTALL(CODE "MESSAGE(\"Done! Please run ${GAME_EXENAME} to start ${GAME_NAME}.\")")
  ENDIF()
ELSE(UNIX)
  SET(GAME_INSTALL_DIR "./data")
ENDIF(UNIX)

