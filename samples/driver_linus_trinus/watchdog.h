#ifndef LINUS_TRINUS_WATCHDOG_H
#define LINUS_TRINUS_WATCHDOG_H

#include <openvr_driver.h>
#include "driverlog.h"

#include <vector>
#include <thread>
#include <chrono>

class CWatchdogDriver_Sample : public vr::IVRWatchdogProvider {
public:
    CWatchdogDriver_Sample();

    virtual vr::EVRInitError Init(vr::IVRDriverContext *pDriverContext);

    virtual void Cleanup();

private:
    std::thread *m_pWatchdogThread;
};

void WatchdogThreadFunction();



#endif //LINUS_TRINUS_WATCHDOG_H
