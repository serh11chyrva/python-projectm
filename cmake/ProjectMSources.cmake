# A release source bundle already contains this directory. Fresh checkouts use
# the same verified archive, extracted into the build tree rather than the repo.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/native-sources.json" _pypm_sources)
string(JSON PYPM_PROJECTM_URL GET "${_pypm_sources}" projectm url)
string(JSON PYPM_PROJECTM_SHA256 GET "${_pypm_sources}" projectm sha256)
set(PYPM_PROJECTM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libprojectM-4.1.6"
    CACHE PATH "Extracted projectM 4.1.6 release sources")
if(NOT EXISTS "${PYPM_PROJECTM_SOURCE_DIR}/CMakeLists.txt")
    include(FetchContent)
    FetchContent_Declare(pypm_projectm
        URL "${PYPM_PROJECTM_URL}"
        URL_HASH "SHA256=${PYPM_PROJECTM_SHA256}"
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        # Download only: add_subdirectory is owned by the root build.
        SOURCE_SUBDIR _pypm_download_only
    )
    FetchContent_MakeAvailable(pypm_projectm)
    set(PYPM_PROJECTM_SOURCE_DIR "${pypm_projectm_SOURCE_DIR}")
endif()
