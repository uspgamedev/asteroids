
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
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

set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -DDEBUG")
if (UNIX OR MINGW)
    # se for o g++ para *nix ou o MinGW para Windows:
    add_definitions(-Wall -ansi -U_FORTIFY_SOURCE -msse2 -DBOOST_HAS_TR1_TUPLE)
elseif (MSVC) 
    add_definitions(/D_CRT_SECURE_NO_WARNINGS /DBOOST_ALL_NO_LIB /DBOOST_HAS_TR1_TUPLE /W4 /wd4100 /wd4127 /wd4201 /wd4211 /wd4250 /wd4706 /arch:SSE2 /fp:fast /MP)
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MD")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /MDd")
endif ()
if(WIN32)
    add_definitions(-DWIN32)
endif()

# LDFLAGS: flags que voce queira enviar ao ligador
SET(LDFLAGS "" CACHE STRING "flags enviadas ao linker")

# se for o g++ para *nix:
IF(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  IF(UNIVERSAL)
    SET(LDFLAGS "${LDFLAGS} -mmacosx-version-min=10.5")
  ENDIF()
ENDIF()


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

find_library (LUGDKD ugdk0.4-dbg lib/)
find_library (LUGDK ugdk0.4 lib/)

if (NOT LUGDK AND NOT LUGDKD)
    message (FATAL_ERROR "Fatal error: libugdk not found!")
endif ()

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

if (PYTHON_DEBUG_LIBRARY)
    set(DEBUGPYLIB debug;${PYTHON_DEBUG_LIBRARY})
else()
    set(DEBUGPYLIB "")
endif()

ADD_EXECUTABLE(${GAME_EXENAME} ${GAME_SRCS})
SET_TARGET_PROPERTIES(${GAME_EXENAME} PROPERTIES LINK_FLAGS "${LDFLAGS}")
SET_TARGET_PROPERTIES(${GAME_EXENAME} PROPERTIES PROJECT_NAME "${GAME_NAME}")
TARGET_LINK_LIBRARIES (${GAME_EXENAME}
                         ${EXTRA_LIBRARIES}
                         optimized ${LUGDK}
                         debug ${LUGDKD}
                         ${SDL_LIBRARY}
                         ${SDLMIXER_LIBRARY}
                         ${SDLTTF_LIBRARY}
                         ${SDLIMAGE_LIBRARY}
                         ${OPENGL_LIBRARIES}
                         optimized ${PYTHON_LIBRARIES}
                         ${DEBUGPYLIB}
                         ${LUA_LIBRARIES}
                        )
