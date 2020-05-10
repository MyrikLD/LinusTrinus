set(TARGET_NAME driver_linus_trinus)

add_library(${TARGET_NAME} SHARED
  driverlog.cpp
  driverlog.h
  driver_linus_trinus.cpp
)

add_definitions(-DDRIVER_SAMPLE_EXPORTS)

target_link_libraries(${TARGET_NAME}
  ${OPENVR_LIBRARIES}
  ${CMAKE_DL_LIBS}
)

set_target_properties(${TARGET_NAME} PROPERTIES PREFIX "")
setTargetOutputDirectory(${TARGET_NAME})
