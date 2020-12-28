#include "socket_process.h"

bool SetSocketBlockingEnabled(int fd, bool blocking) {
    if (fd < 0) return false;

#ifdef _WIN32
    unsigned long mode = blocking ? 0 : 1;
    return ioctlsocket(fd, FIONBIO, &mode) == 0;
#else
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return false;
    flags = blocking ? (flags & ~O_NONBLOCK) : (flags | O_NONBLOCK);
    return fcntl(fd, F_SETFL, flags) == 0;
#endif
}

void create_socket_thread(ThreadState *state, int port = 4242) {
    struct sockaddr_in local;
    memset((char *) &local, 0, sizeof(local));

    local.sin_family = AF_INET;
    local.sin_port = htons(port);
    local.sin_addr.s_addr = htonl(INADDR_ANY);

    state->socketS = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    SetSocketBlockingEnabled(state->socketS, true);

    int iResult = bind(state->socketS, (struct sockaddr *) &local, sizeof(local));

    if (iResult < 0) {
        DriverLog("linus_trinus: Socket activation error: %d\n", iResult);
        state->SocketActivated = false;
    } else {
        DriverLog("linus_trinus: Socket activated\n");
        state->SocketActivated = true;
        state->thread = new std::thread(SockReadFunc, state);
    }
}

void SockReadFunc(ThreadState *state) {
    DriverLog("linus_trinus: Sock run\n");

    int bytes_read = 0;
    socklen_t fromlen;
    struct sockaddr_in from;

    while (state->SocketActivated) {
        memset(&state->OpenTrack, 0, sizeof(state->OpenTrack));
        state->bKeepReading = true;
        while (state->bKeepReading) {
            bytes_read = recvfrom(
                    state->socketS,
                    (char *) (&state->OpenTrack),
                    sizeof(state->OpenTrack),
                    0,
                    (sockaddr *) &from,
                    &fromlen
            );
            if (!bytes_read) {
                state->bKeepReading = false;
                DriverLog("linus_trinus: bKeepReading=false\n");
            }
        }
    }
}

