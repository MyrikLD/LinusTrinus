#ifndef LINUS_TRINUS_SOCKET_PROCESS_H
#define LINUS_TRINUS_SOCKET_PROCESS_H

#include <sys/types.h>
#include <sys/socket.h>
#include <cmath>
#include <unistd.h>
#include <fcntl.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <cstring>
#include <thread>

#include "driverlog.h"
#include <openvr_driver.h>

#ifndef _WIN32
#define SOCKET int
#endif

using namespace vr;

inline HmdQuaternion_t HmdQuaternion_Init(double w, double x, double y, double z) {
    HmdQuaternion_t quat;
    quat.w = w;
    quat.x = x;
    quat.y = y;
    quat.z = z;
    return quat;
}

struct ThreadState {
    HmdQuaternion_t OpenTrack{0, 0, 0, 0};
    SOCKET socketS = 0;
    std::thread *thread = nullptr;
    bool SocketActivated = false;
    bool bKeepReading = false;

    void destroy() {
        if (SocketActivated) {
            SocketActivated = false;
            if (thread) {
                thread->join();
                delete thread;
                thread = nullptr;
            }
            close(socketS);
        }
    }
};

bool SetSocketBlockingEnabled(int fd, bool blocking);

void SockReadFunc(ThreadState *state);

void create_socket_thread(ThreadState *state, int port);

#endif //LINUS_TRINUS_SOCKET_PROCESS_H
