
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)
PROJECT(asteroids CXX C)
SET(GAME_EXENAME asteroids_wars)
SET(GAME_NAME "Asteroids Wars")

set (ASTEROIDS_VERSION_MAJOR 1)
set (ASTEROIDS_VERSION_MINOR 0)
set (ASTEROIDS_VERSION_PATCH 0)
set (ASTEROIDS_BIGVERSION ${ASTEROIDS_VERSION_MAJOR}.${ASTEROIDS_VERSION_MINOR})
set (ASTEROIDS_VERSION "${ASTEROIDS_BIGVERSION}.${ASTEROIDS_VERSION_PATCH} Beta")

set(GROUP_NAME "USPGameDev Team")
set(HOME_URL "http://uspgamedev.org/")
set(CONTACT_MAIL "admin@uspgamedev.org")

# Arquivos de codigo fonte vao aqui!
SET(GAME_SRCS 
    ./src/asteroids.cc 
)

IF (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    SET(GAME_SRCS ${GAME_SRCS} src/mac/SDLMain.h src/mac/SDLMain.m)
ENDIF ()

MESSAGE("${GAME_NAME} version ${ASTEROIDS_VERSION}")

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

find_library (LUGDK ugdk0.4 lib/)

if (NOT LUGDK)
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
                         ${LUGDK}                         
                         ${SDL_LIBRARY}
                         ${SDLMIXER_LIBRARY}
                         ${SDLTTF_LIBRARY}
                         ${SDLIMAGE_LIBRARY}
                         ${OPENGL_LIBRARIES}
                         optimized ${PYTHON_LIBRARIES}
                         ${DEBUGPYLIB}
                         ${LUA_LIBRARIES}
                        )

##########################################
# Package Configuration

set (CPACK_GENERATOR DEB)
set (CPACK_PACKAGE_DESCRIPTION_FILE README.txt)
set (CPACK_PACKAGE_NAME asteroids_wars)
set (CPACK_PACKAGE_VENDOR ${GROUP_NAME})
set (CPACK_PACKAGE_CONTACT "${GROUP_NAME} <${CONTACT_MAIL}>")
set (CPACK_PACKAGE_INSTALL_REGISTRY_KEY "asteroids_wars")
set (CPACK_PACKAGE_VERSION_MAJOR ${ASTEROIDS_VERSION_MAJOR})
set (CPACK_PACKAGE_VERSION_MINOR ${ASTEROIDS_VERSION_MINOR})
set (CPACK_PACKAGE_VERSION_PATCH ${ASTEROIDS_VERSION_PATCH})
set (CPACK_PACKAGE_DESCRIPTION_SUMMARY "Simple, crazy and fun asteroids-like game made by USPGameDev.")
set (CPACK_DEBIAN_PACKAGE_NAME "asteroids_wars")
set (CPACK_DEBIAN_PACKAGE_HOMEPAGE ${HOME_URL})
set (CPACK_DEBIAN_PACKAGE_DEPENDS "libc6 (>= 2.2), libgcc1 (>= 1:4.1.1), libstdc++6 (>= 4.4.0), libsdl1.2, libsdl-image1.2, libsdl-mixer1.2, libsdl-ttf2.0-0, python (>= 2.6)")
set (DEBIAN_PACKAGE_BUILDS_DEPENDS "libc6 (>= 2.2), libgcc1 (>= 1:4.1.1), libstdc++6 (>= 4.4.0), libugdk0.4, python-dev (>= 2.6), cmake")
set (CPACK_NSIS_CONTACT ${CONTACT_MAIL})
set (CPACK_NSIS_DISPLAY_NAME ${GAME_NAME})
set (CPACK_NSIS_PACKAGE_HOMEPAGE ${HOME_URL})
set (CPACK_RPM_PACKAGE_ARCHITECTURE ${CMAKE_SYSTEM_PROCESSOR})
set (CPACK_RPM_PACKAGE_URL ${HOME_URL})

include (CPack)

#
##########################################
