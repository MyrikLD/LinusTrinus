//============ Copyright (c) Valve Corporation, All rights reserved. ============

#include <openvr_driver.h>
#include "driverlog.h"

#include <vector>
#include <thread>
#include <chrono>

#if defined( _WINDOWS )
#include <windows.h>
#else
#include <sys/types.h>
#include <sys/socket.h>
#include <math.h>
#include <unistd.h>
#include <fcntl.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <string.h>
#endif

#ifndef _WIN32
int SOCKET_ERROR = SO_ERROR;
int INVALID_SOCKET = SOL_SOCKET;
#define SOCKET int
#endif
bool SocketActivated = false;
bool bKeepReading = false;
SOCKET socketS;
struct sockaddr_in from;
socklen_t  fromlen;
std::thread *pSocketThread = NULL;
int bytes_read;


using namespace vr;


#if defined(_WIN32)
#define HMD_DLL_EXPORT extern "C" __declspec( dllexport )
#define HMD_DLL_IMPORT extern "C" __declspec( dllimport )
#elif defined(__GNUC__) || defined(COMPILER_GCC) || defined(__APPLE__)
#define HMD_DLL_EXPORT extern "C" __attribute__((visibility("default")))
#define HMD_DLL_IMPORT extern "C"
#else
#error "Unsupported Platform."
#endif

HmdQuaternion_t OpenTrack;

inline HmdQuaternion_t HmdQuaternion_Init( double w, double x, double y, double z )
{
    HmdQuaternion_t quat;
    quat.w = w;
    quat.x = x;
    quat.y = y;
    quat.z = z;
    return quat;
}

inline void HmdMatrix_SetIdentity( HmdMatrix34_t *pMatrix )
{
    pMatrix->m[0][0] = 1.f;
    pMatrix->m[0][1] = 0.f;
    pMatrix->m[0][2] = 0.f;
    pMatrix->m[0][3] = 0.f;
    pMatrix->m[1][0] = 0.f;
    pMatrix->m[1][1] = 1.f;
    pMatrix->m[1][2] = 0.f;
    pMatrix->m[1][3] = 0.f;
    pMatrix->m[2][0] = 0.f;
    pMatrix->m[2][1] = 0.f;
    pMatrix->m[2][2] = 1.f;
    pMatrix->m[2][3] = 0.f;
}


// keys for use with the settings API
static const char * const k_pch_Sample_Section = "linus_trinus";
static const char * const k_pch_Sample_SerialNumber_String = "serialNumber";
static const char * const k_pch_Sample_ModelNumber_String = "modelNumber";
static const char * const k_pch_Sample_WindowX_Int32 = "windowX";
static const char * const k_pch_Sample_WindowY_Int32 = "windowY";
static const char * const k_pch_Sample_WindowWidth_Int32 = "windowWidth";
static const char * const k_pch_Sample_WindowHeight_Int32 = "windowHeight";
static const char * const k_pch_Sample_RenderWidth_Int32 = "renderWidth";
static const char * const k_pch_Sample_RenderHeight_Int32 = "renderHeight";
static const char * const k_pch_Sample_SecondsFromVsyncToPhotons_Float = "secondsFromVsyncToPhotons";
static const char * const k_pch_Sample_DisplayFrequency_Float = "displayFrequency";

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------

class CWatchdogDriver_Sample : public IVRWatchdogProvider
{
public:
    CWatchdogDriver_Sample()
    {
        m_pWatchdogThread = nullptr;
    }

    virtual EVRInitError Init( vr::IVRDriverContext *pDriverContext ) ;
    virtual void Cleanup() ;

private:
    std::thread *m_pWatchdogThread;
};

CWatchdogDriver_Sample g_watchdogDriverNull;


bool g_bExiting = false;

void WatchdogThreadFunction(  )
{
    while ( !g_bExiting )
    {
#if defined( _WINDOWS )
        // on windows send the event when the Y key is pressed.
        if ( (0x01 & GetAsyncKeyState( 'Y' )) != 0 )
        {
            // Y key was pressed.
            vr::VRWatchdogHost()->WatchdogWakeUp();
        }
        std::this_thread::sleep_for( std::chrono::microseconds( 500 ) );
#else
        // for the other platforms, just send one every five seconds
        std::this_thread::sleep_for( std::chrono::seconds( 5 ) );
        vr::VRWatchdogHost()->WatchdogWakeUp(TrackedDeviceClass_HMD);
#endif
    }
}

EVRInitError CWatchdogDriver_Sample::Init( vr::IVRDriverContext *pDriverContext )
{
    VR_INIT_WATCHDOG_DRIVER_CONTEXT( pDriverContext );
    InitDriverLog( vr::VRDriverLog() );

    // Watchdog mode on Windows starts a thread that listens for the 'Y' key on the keyboard to
    // be pressed. A real driver should wait for a system button event or something else from the
    // the hardware that signals that the VR system should start up.
    g_bExiting = false;
    m_pWatchdogThread = new std::thread( WatchdogThreadFunction );
    if ( !m_pWatchdogThread )
    {
        DriverLog( "Unable to create watchdog thread\n");
        return VRInitError_Driver_Failed;
    }

    return VRInitError_None;
}


void CWatchdogDriver_Sample::Cleanup()
{
    g_bExiting = true;
    if ( m_pWatchdogThread )
    {
        m_pWatchdogThread->join();
        delete m_pWatchdogThread;
        m_pWatchdogThread = nullptr;
    }

    CleanupDriverLog();
}

/** Returns true on success, or false if there was an error */
bool SetSocketBlockingEnabled(int fd, bool blocking)
{
    if (fd < 0) return false;

#ifdef _WIN32
    unsigned long mode = blocking ? 0 : 1;
    return (ioctlsocket(fd, FIONBIO, &mode) == 0) ? true : false;
#else
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return false;
    flags = blocking ? (flags & ~O_NONBLOCK) : (flags | O_NONBLOCK);
    return (fcntl(fd, F_SETFL, flags) == 0) ? true : false;
#endif
}


void WinSockReadFunc()
{
    DriverLog( "linus_trinus: Sock run\n");
    while (SocketActivated) {
        //Read UDP socket with OpenTrack data
        memset(&OpenTrack, 0, sizeof(OpenTrack));
        bKeepReading = true;
        while (bKeepReading) {
            bytes_read = recvfrom(socketS, (char*)(&OpenTrack), sizeof(OpenTrack), 0, (sockaddr*)&from, &fromlen);
            if (bytes_read > 0) {
                //Yaw = DegToRad(OpenTrack.Yaw);
                //Pitch = DegToRad(OpenTrack.Pitch);
                //Roll = DegToRad(OpenTrack.Roll);

                //toQuaternion(&OpenTrack);
                //DriverLog( "linus_trinus: Data read: %f %f %f\n", Yaw, Pitch, Roll);
                //Convert yaw, pitch, roll to quaternion
                //qW = cos(Yaw * 0.5) * cos(Roll * 0.5) * cos(Pitch * 0.5) + sin(Yaw * 0.5) * sin(Roll * 0.5) * sin(Pitch * 0.5);
                //qX = cos(Yaw * 0.5) * sin(Roll * 0.5) * cos(Pitch * 0.5) - sin(Yaw * 0.5) * cos(Roll * 0.5) * sin(Pitch * 0.5);
                //qY = cos(Yaw * 0.5) * cos(Roll * 0.5) * sin(Pitch * 0.5) + sin(Yaw * 0.5) * sin(Roll * 0.5) * cos(Pitch * 0.5);
                //qZ = sin(Yaw * 0.5) * cos(Roll * 0.5) * cos(Pitch * 0.5) - cos(Yaw * 0.5) * sin(Roll * 0.5) * sin(Pitch * 0.5);
            } else {
                bKeepReading = false;
                DriverLog( "linus_trinus: bKeepReading=false\n");
            }
        }
    }
}

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------
class CSampleDeviceDriver : public vr::ITrackedDeviceServerDriver, public vr::IVRDisplayComponent
{
public:
    CSampleDeviceDriver(  )
    {
        m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
        m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

        DriverLog( "linus_trinus: Using settings values\n" );
        m_flIPD = vr::VRSettings()->GetFloat( k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float );

        char buf[1024];
        //vr::VRSettings()->GetString( k_pch_Sample_Section, k_pch_Sample_SerialNumber_String, buf, sizeof( buf ) );
        //m_sSerialNumber = buf;
        m_sSerialNumber = "udp_device";

        vr::VRSettings()->GetString( k_pch_Sample_Section, k_pch_Sample_ModelNumber_String, buf, sizeof( buf ) );
        m_sModelNumber = buf;

        m_nWindowX = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_WindowX_Int32 );
        m_nWindowY = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_WindowY_Int32 );
        m_nWindowWidth = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_WindowWidth_Int32 );
        m_nWindowHeight = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_WindowHeight_Int32 );
        m_nRenderWidth = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_RenderWidth_Int32 );
        m_nRenderHeight = vr::VRSettings()->GetInt32( k_pch_Sample_Section, k_pch_Sample_RenderHeight_Int32 );
        m_flSecondsFromVsyncToPhotons = vr::VRSettings()->GetFloat( k_pch_Sample_Section, k_pch_Sample_SecondsFromVsyncToPhotons_Float );
        m_flDisplayFrequency = vr::VRSettings()->GetFloat( k_pch_Sample_Section, k_pch_Sample_DisplayFrequency_Float );

        DriverLog( "linus_trinus: Serial Number: %s\n", m_sSerialNumber.c_str() );
        DriverLog( "linus_trinus: Model Number: %s\n", m_sModelNumber.c_str() );
        DriverLog( "linus_trinus: Window: %d %d %d %d\n", m_nWindowX, m_nWindowY, m_nWindowWidth, m_nWindowHeight );
        DriverLog( "linus_trinus: Render Target: %d %d\n", m_nRenderWidth, m_nRenderHeight );
        DriverLog( "linus_trinus: Seconds from Vsync to Photons: %f\n", m_flSecondsFromVsyncToPhotons );
        DriverLog( "linus_trinus: Display Frequency: %f\n", m_flDisplayFrequency );
        DriverLog( "linus_trinus: IPD: %f\n", m_flIPD );
        DriverLog( "linus_trinus: RUN\n" );

        struct sockaddr_in local;
        memset((char *) &local, 0, sizeof(local));
        local.sin_family = AF_INET;
        local.sin_port = htons(4242);
        local.sin_addr.s_addr = htonl(INADDR_ANY);
        int iResult;
        socketS = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
        SetSocketBlockingEnabled(socketS, true);
        iResult = bind(socketS, (struct sockaddr*)&local, sizeof(local));
        if (iResult<0){
            DriverLog( "linus_trinus: Socket activation error: %d\n", iResult );
            SocketActivated = false;
        } else {
            DriverLog( "linus_trinus: Socket activated\n" );
            SocketActivated = true;
            pSocketThread = new std::thread(WinSockReadFunc);
        }
    }

    virtual ~CSampleDeviceDriver()
    {
    }


    virtual EVRInitError Activate( vr::TrackedDeviceIndex_t unObjectId )
    {
        m_unObjectId = unObjectId;
        m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer( m_unObjectId );


        vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, Prop_ModelNumber_String, m_sModelNumber.c_str() );
        vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, Prop_RenderModelName_String, m_sModelNumber.c_str() );
        vr::VRProperties()->SetFloatProperty( m_ulPropertyContainer, Prop_UserIpdMeters_Float, m_flIPD );
        vr::VRProperties()->SetFloatProperty( m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, 0.f );
        vr::VRProperties()->SetFloatProperty( m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency );
        vr::VRProperties()->SetFloatProperty( m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float, m_flSecondsFromVsyncToPhotons );

        // return a constant that's not 0 (invalid) or 1 (reserved for Oculus)
        vr::VRProperties()->SetUint64Property( m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2 );

        // avoid "not fullscreen" warnings from vrmonitor
        vr::VRProperties()->SetBoolProperty( m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false );

        // Icons can be configured in code or automatically configured by an external file "drivername\resources\driver.vrresources".
        // Icon properties NOT configured in code (post Activate) are then auto-configured by the optional presence of a driver's "drivername\resources\driver.vrresources".
        // In this manner a driver can configure their icons in a flexible data driven fashion by using an external file.
        //
        // The structure of the driver.vrresources file allows a driver todriver.vrresources specialize their icons based on tdriver.vrresourcesheir HW.
        // Keys matching the value in "Prop_ModelNumber_String" are considered first, since the driver may have model specific icons.
        // An absence of a matching "Prop_ModelNumber_String" then considers the ETrackedDeviceClass ("HMD", "Controller", "GenericTracker", "TrackingReference")
        // since the driver may have specialized icons based on those device class names.
        //
        // An absence of either then falls back to the "system.vrresources" where generic device class icons are then supplied.
        //
        // Please refer to "bin\drivers\sample\resources\driver.vrresources" which contains this sample configuration.
        //
        // "Alias" is a reserved key and specifies chaining to another json block.
        //
        // In this sample configuration file (overly complex FOR EXAMPLE PURPOSES ONLY)....
        //
        // "Model-v2.0" chains through the alias to "Model-v1.0" which chains through the alias to "Model-v Defaults".
        //
        // Keys NOT found in "Model-v2.0" would then chase through the "Alias" to be resolved in "Model-v1.0" and either resolve their or continue through the alias.
        // Thus "Prop_NamedIconPathDeviceAlertLow_String" in each model's block represent a specialization specific for that "model".
        // Keys in "Model-v Defaults" are an example of mapping to the same states, and here all map to "Prop_NamedIconPathDeviceOff_String".
        //
        bool bSetupIconUsingExternalResourceFile = true;
        if ( !bSetupIconUsingExternalResourceFile )
        {
            // Setup properties directly in code.
            // Path values are of the form {drivername}\icons\some_icon_filename.png
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceOff_String, "{linus_trinus}/icons/headset_sample_status_off.png" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearching_String, "{linus_trinus}/icons/headset_sample_status_searching.gif" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearchingAlert_String, "{linus_trinus}/icons/headset_sample_status_searching_alert.gif" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReady_String, "{linus_trinus}/icons/headset_sample_status_ready.png" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReadyAlert_String, "{linus_trinus}/icons/headset_sample_status_ready_alert.png" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceNotReady_String, "{linus_trinus}/icons/headset_sample_status_error.png" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceStandby_String, "{linus_trinus}/icons/headset_sample_status_standby.png" );
            vr::VRProperties()->SetStringProperty( m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceAlertLow_String, "{linus_trinus}/icons/headset_sample_status_ready_low.png" );
        }

        return VRInitError_None;
    }

    virtual void Deactivate()
    {
        m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    }

    virtual void EnterStandby()
    {
    }

    void *GetComponent( const char *pchComponentNameAndVersion )
    {
        if ( !_stricmp( pchComponentNameAndVersion, vr::IVRDisplayComponent_Version ) )
        {
            return (vr::IVRDisplayComponent*)this;
        }

        // override this to add a component to a driver
        return NULL;
    }

    virtual void PowerOff()
    {
    }

    /** debug request from a client */
    virtual void DebugRequest( const char *pchRequest, char *pchResponseBuffer, uint32_t unResponseBufferSize )
    {
        if( unResponseBufferSize >= 1 )
            pchResponseBuffer[0] = 0;
    }

    virtual void GetWindowBounds( int32_t *pnX, int32_t *pnY, uint32_t *pnWidth, uint32_t *pnHeight )
    {
        *pnX = m_nWindowX;
        *pnY = m_nWindowY;
        *pnWidth = m_nWindowWidth;
        *pnHeight = m_nWindowHeight;
    }

    virtual bool IsDisplayOnDesktop()
    {
        return true;
    }

    virtual bool IsDisplayRealDisplay()
    {
        return false;
    }

    virtual void GetRecommendedRenderTargetSize( uint32_t *pnWidth, uint32_t *pnHeight )
    {
        *pnWidth = m_nRenderWidth;
        *pnHeight = m_nRenderHeight;
    }

    virtual void GetEyeOutputViewport( EVREye eEye, uint32_t *pnX, uint32_t *pnY, uint32_t *pnWidth, uint32_t *pnHeight )
    {
        *pnY = 0;
        *pnWidth = m_nWindowWidth / 2;
        *pnHeight = m_nWindowHeight;

        if ( eEye == Eye_Left )
        {
            *pnX = 0;
        }
        else
        {
            *pnX = m_nWindowWidth / 2;
        }
    }

    virtual void GetProjectionRaw( EVREye eEye, float *pfLeft, float *pfRight, float *pfTop, float *pfBottom )
    {
        *pfLeft = -1.0;
        *pfRight = 1.0;
        *pfTop = -1.0;
        *pfBottom = 1.0;
    }

    virtual DistortionCoordinates_t ComputeDistortion( EVREye eEye, float fU, float fV )
    {
        DistortionCoordinates_t coordinates;
        coordinates.rfBlue[0] = fU;
        coordinates.rfBlue[1] = fV;
        coordinates.rfGreen[0] = fU;
        coordinates.rfGreen[1] = fV;
        coordinates.rfRed[0] = fU;
        coordinates.rfRed[1] = fV;
        return coordinates;
    }

    virtual DriverPose_t GetPose()
    {
        DriverPose_t pose = { 0 };

        if (SocketActivated) {
            pose.poseIsValid = true;
            pose.result = TrackingResult_Running_OK;
            pose.deviceIsConnected = true;
        }
        else
        {
            pose.poseIsValid = false;
            pose.result = TrackingResult_Uninitialized;
            pose.deviceIsConnected = false;
        }

        pose.qWorldFromDriverRotation = HmdQuaternion_Init( 1, 0, 0, 0 );
        pose.qDriverFromHeadRotation = HmdQuaternion_Init( 1, 0, 0, 0 );

        //Set head tracking rotation
//        pose.qRotation.w = qW;
//        pose.qRotation.x = qX;
//        pose.qRotation.y = qY;
//        pose.qRotation.z = qZ;

        pose.qRotation = OpenTrack;

        //Set position tracking
        // pose.vecPosition[0] = pX * 0.01;
        // pose.vecPosition[1] = pY * 0.01;
        // pose.vecPosition[2] = pZ * 0.01;

        return pose;
    }


    void RunFrame()
    {
        // In a real driver, this should happen from some pose tracking thread.
        // The RunFrame interval is unspecified and can be very irregular if some other
        // driver blocks it for some periodic task.
        if ( m_unObjectId != vr::k_unTrackedDeviceIndexInvalid )
        {
            vr::VRServerDriverHost()->TrackedDevicePoseUpdated( m_unObjectId, GetPose(), sizeof( DriverPose_t ) );
        }
    }

    std::string GetSerialNumber() const { return m_sSerialNumber; }

private:
    vr::TrackedDeviceIndex_t m_unObjectId;
    vr::PropertyContainerHandle_t m_ulPropertyContainer;

    std::string m_sSerialNumber;
    std::string m_sModelNumber;

    int32_t m_nWindowX;
    int32_t m_nWindowY;
    int32_t m_nWindowWidth;
    int32_t m_nWindowHeight;
    int32_t m_nRenderWidth;
    int32_t m_nRenderHeight;
    float m_flSecondsFromVsyncToPhotons;
    float m_flDisplayFrequency;
    float m_flIPD;
};

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------
class CServerDriver_Sample: public IServerTrackedDeviceProvider
{
public:
    CServerDriver_Sample()
        : m_pNullHmdLatest( NULL )
        , m_bEnableNullDriver( true )
    {
    }

    virtual EVRInitError Init( vr::IVRDriverContext *pDriverContext ) ;
    virtual void Cleanup() ;
    virtual const char * const *GetInterfaceVersions() { return vr::k_InterfaceVersions; }
    virtual void RunFrame() ;
    virtual bool ShouldBlockStandbyMode()  { return false; }
    virtual void EnterStandby()  {}
    virtual void LeaveStandby()  {}

private:
    CSampleDeviceDriver *m_pNullHmdLatest;

    bool m_bEnableNullDriver;
};

CServerDriver_Sample g_serverDriverNull;


EVRInitError CServerDriver_Sample::Init( vr::IVRDriverContext *pDriverContext )
{
    VR_INIT_SERVER_DRIVER_CONTEXT( pDriverContext );
    InitDriverLog( vr::VRDriverLog() );

    m_pNullHmdLatest = new CSampleDeviceDriver();

    DriverLog( ": Add device: %s\n", m_pNullHmdLatest->GetSerialNumber().c_str());

    vr::VRServerDriverHost()->TrackedDeviceAdded( m_pNullHmdLatest->GetSerialNumber().c_str(), vr::TrackedDeviceClass_HMD, m_pNullHmdLatest );
    return VRInitError_None;
}

void CServerDriver_Sample::Cleanup()
{
    //Close UDP
    if (SocketActivated) {
        SocketActivated = false;
        if (pSocketThread) {
            pSocketThread->join();
            delete pSocketThread;
            pSocketThread = nullptr;
        }
        close(socketS);
    }
    CleanupDriverLog();
    delete m_pNullHmdLatest;
    m_pNullHmdLatest = NULL;
}


void CServerDriver_Sample::RunFrame()
{
    if ( m_pNullHmdLatest )
    {
        m_pNullHmdLatest->RunFrame();
    }
}

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------
HMD_DLL_EXPORT void *HmdDriverFactory( const char *pInterfaceName, int *pReturnCode )
{
    if( 0 == strcmp( IServerTrackedDeviceProvider_Version, pInterfaceName ) )
    {
        return &g_serverDriverNull;
    }
    if( 0 == strcmp( IVRWatchdogProvider_Version, pInterfaceName ) )
    {
        return &g_watchdogDriverNull;
    }

    if( pReturnCode )
        *pReturnCode = VRInitError_Init_InterfaceNotFound;

    return NULL;
}
