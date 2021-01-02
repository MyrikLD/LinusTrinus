//============ Copyright (c) Valve Corporation, All rights reserved. ============

#include "driver_linus_trinus.h"
#include "socket_process.h"

#include <vector>
#include <thread>
#include <chrono>

#if defined( _WINDOWS )
#include <windows.h>
#else

#include <sys/types.h>
#include <cstring>

#endif

#include "OvrController.h"

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

ThreadState *threadState = new ThreadState();

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------
class CSampleDeviceDriver : public vr::ITrackedDeviceServerDriver, public vr::IVRDisplayComponent {
public:
    CSampleDeviceDriver() {
        m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
        m_ulPropertyContainer = vr::k_ulInvalidPropertyContainer;

        DriverLog("linus_trinus: Using settings values\n");
        m_flIPD = vr::VRSettings()->GetFloat(k_pch_SteamVR_Section, k_pch_SteamVR_IPD_Float);

        char buf[1024];
        //vr::VRSettings()->GetString( k_pch_Section, k_pch_SerialNumber_String, buf, sizeof( buf ) );
        //m_sSerialNumber = buf;
        m_sSerialNumber = "udp_device";

        vr::VRSettings()->GetString(k_pch_Section, k_pch_ModelNumber_String, buf, sizeof(buf));
        m_sModelNumber = buf;

        m_nWindowX = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_WindowX_Int32);
        m_nWindowY = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_WindowY_Int32);
        m_nWindowWidth = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_WindowWidth_Int32);
        m_nWindowHeight = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_WindowHeight_Int32);
        m_nRenderWidth = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_RenderWidth_Int32);
        m_nRenderHeight = vr::VRSettings()->GetInt32(k_pch_Section, k_pch_RenderHeight_Int32);
        m_flSecondsFromVsyncToPhotons = vr::VRSettings()->GetFloat(k_pch_Section,
                                                                   k_pch_SecondsFromVsyncToPhotons_Float);
        m_flDisplayFrequency = vr::VRSettings()->GetFloat(k_pch_Section, k_pch_DisplayFrequency_Float);

        DriverLog("linus_trinus: Serial Number: %s\n", m_sSerialNumber.c_str());
        DriverLog("linus_trinus: Model Number: %s\n", m_sModelNumber.c_str());
        DriverLog("linus_trinus: Window: %d %d %d %d\n", m_nWindowX, m_nWindowY, m_nWindowWidth, m_nWindowHeight);
        DriverLog("linus_trinus: Render Target: %d %d\n", m_nRenderWidth, m_nRenderHeight);
        DriverLog("linus_trinus: Seconds from Vsync to Photons: %f\n", m_flSecondsFromVsyncToPhotons);
        DriverLog("linus_trinus: Display Frequency: %f\n", m_flDisplayFrequency);
        DriverLog("linus_trinus: IPD: %f\n", m_flIPD);
        DriverLog("linus_trinus: RUN\n");

        bool ret;
        m_leftController = new OvrController(true, 0);
        ret = VRServerDriverHost()->TrackedDeviceAdded(
                m_leftController->GetSerialNumber().c_str(),
                vr::TrackedDeviceClass_Controller,
                m_leftController
        );

        m_rightController = new OvrController(false, 1);
        ret = VRServerDriverHost()->TrackedDeviceAdded(
                m_rightController->GetSerialNumber().c_str(),
                vr::TrackedDeviceClass_Controller,
                m_rightController
        );

        create_socket_thread(threadState, 4242);
    }

    virtual ~CSampleDeviceDriver() = default;


    EVRInitError Activate(vr::TrackedDeviceIndex_t unObjectId) override {
        m_unObjectId = unObjectId;
        m_ulPropertyContainer = vr::VRProperties()->TrackedDeviceToPropertyContainer(m_unObjectId);


        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_ModelNumber_String, m_sModelNumber.c_str());
        vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, Prop_RenderModelName_String,
                                              m_sModelNumber.c_str());
        vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserIpdMeters_Float, m_flIPD);
        vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_UserHeadToEyeDepthMeters_Float, 0.f);
        vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_DisplayFrequency_Float, m_flDisplayFrequency);
        vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, Prop_SecondsFromVsyncToPhotons_Float,
                                             m_flSecondsFromVsyncToPhotons);

        // return a constant that's not 0 (invalid) or 1 (reserved for Oculus)
        vr::VRProperties()->SetUint64Property(m_ulPropertyContainer, Prop_CurrentUniverseId_Uint64, 2);

        // avoid "not fullscreen" warnings from vrmonitor
        vr::VRProperties()->SetBoolProperty(m_ulPropertyContainer, Prop_IsOnDesktop_Bool, false);

        bool bSetupIconUsingExternalResourceFile = true;
        if (!bSetupIconUsingExternalResourceFile) {
            // Setup properties directly in code.
            // Path values are of the form {drivername}\icons\some_icon_filename.png
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceOff_String,
                                                  "{linus_trinus}/icons/headset_sample_status_off.png");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceSearching_String,
                                                  "{linus_trinus}/icons/headset_sample_status_searching.gif");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer,
                                                  vr::Prop_NamedIconPathDeviceSearchingAlert_String,
                                                  "{linus_trinus}/icons/headset_sample_status_searching_alert.gif");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReady_String,
                                                  "{linus_trinus}/icons/headset_sample_status_ready.png");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceReadyAlert_String,
                                                  "{linus_trinus}/icons/headset_sample_status_ready_alert.png");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceNotReady_String,
                                                  "{linus_trinus}/icons/headset_sample_status_error.png");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceStandby_String,
                                                  "{linus_trinus}/icons/headset_sample_status_standby.png");
            vr::VRProperties()->SetStringProperty(m_ulPropertyContainer, vr::Prop_NamedIconPathDeviceAlertLow_String,
                                                  "{linus_trinus}/icons/headset_sample_status_ready_low.png");
        }

        return VRInitError_None;
    }

    void Deactivate() override {
        m_unObjectId = vr::k_unTrackedDeviceIndexInvalid;
    }

    void EnterStandby() override {
    }

    void *GetComponent(const char *pchComponentNameAndVersion) override {
        if (!strcmp(pchComponentNameAndVersion, vr::IVRDisplayComponent_Version)) {
            return (vr::IVRDisplayComponent *) this;
        }
        if (!strcmp(pchComponentNameAndVersion, vr::IVRCameraComponent_Version)) {
            return (vr::IVRCameraComponent *) this;
        }

        return nullptr;
    }

    /** debug request from a client */
    void DebugRequest(const char *pchRequest, char *pchResponseBuffer, uint32_t unResponseBufferSize) override {
        if (unResponseBufferSize >= 1)
            pchResponseBuffer[0] = 0;
    }

    void GetWindowBounds(int32_t *pnX, int32_t *pnY, uint32_t *pnWidth, uint32_t *pnHeight) override {
        *pnX = m_nWindowX;
        *pnY = m_nWindowY;
        *pnWidth = m_nWindowWidth;
        *pnHeight = m_nWindowHeight;
    }

    bool IsDisplayOnDesktop() override {
        return true;
    }

    bool IsDisplayRealDisplay() override {
        return false;
    }

    void GetRecommendedRenderTargetSize(uint32_t *pnWidth, uint32_t *pnHeight) override {
        *pnWidth = m_nRenderWidth;
        *pnHeight = m_nRenderHeight;
    }

    void
    GetEyeOutputViewport(EVREye eEye, uint32_t *pnX, uint32_t *pnY, uint32_t *pnWidth, uint32_t *pnHeight) override {
        *pnY = 0;
        *pnWidth = m_nWindowWidth / 2;
        *pnHeight = m_nWindowHeight;

        if (eEye == Eye_Left) {
            *pnX = 0;
        } else {
            *pnX = m_nWindowWidth / 2;
        }
    }

    void GetProjectionRaw(EVREye eEye, float *pfLeft, float *pfRight, float *pfTop, float *pfBottom) override {
        *pfLeft = -1.0;
        *pfRight = 1.0;
        *pfTop = -1.0;
        *pfBottom = 1.0;
    }

    DistortionCoordinates_t ComputeDistortion(EVREye eEye, float fU, float fV) override {
        DistortionCoordinates_t coordinates;
        coordinates.rfBlue[0] = fU;
        coordinates.rfBlue[1] = fV;
        coordinates.rfGreen[0] = fU;
        coordinates.rfGreen[1] = fV;
        coordinates.rfRed[0] = fU;
        coordinates.rfRed[1] = fV;
        return coordinates;
    }

    DriverPose_t GetPose() override {
        DriverPose_t pose = {0};

        pose.qWorldFromDriverRotation = HmdQuaternion_Init(1, 0, 0, 0);
        pose.qDriverFromHeadRotation = HmdQuaternion_Init(1, 0, 0, 0);
        pose.qRotation = HmdQuaternion_Init(1, 0, 0, 0);

        if (threadState->SocketActivated) {
            pose.poseIsValid = true;
            pose.result = TrackingResult_Running_OK;
            pose.deviceIsConnected = true;
        } else {
            pose.poseIsValid = false;
            pose.result = TrackingResult_Uninitialized;
            pose.deviceIsConnected = false;
            return pose;
        }

        if (threadState->SocketActivated) {

            TrackingInfo info = threadState->tracking_info;

            pose.qRotation = HmdQuaternion_Init(info.HeadPose_Pose_Orientation.w,
                                                info.HeadPose_Pose_Orientation.x,
                                                info.HeadPose_Pose_Orientation.y,
                                                info.HeadPose_Pose_Orientation.z);


            pose.vecPosition[0] = info.HeadPose_Pose_Position.x;
            pose.vecPosition[1] = info.HeadPose_Pose_Position.y;
            pose.vecPosition[2] = info.HeadPose_Pose_Position.z;

            // set battery percentage
            vr::VRProperties()->SetFloatProperty(m_ulPropertyContainer, vr::Prop_DeviceBatteryPercentage_Float,
                                                 info.battery / 100.0f);

            // To disable time warp (or pose prediction), we dont set (set to zero) velocity and acceleration.

            pose.poseTimeOffset = 0;

            m_leftController->onPoseUpdate(0, info);
            m_rightController->onPoseUpdate(1, info);
        }



        return pose;
    }


    void RunFrame() {
        if (m_unObjectId != vr::k_unTrackedDeviceIndexInvalid) {
            vr::VRServerDriverHost()->TrackedDevicePoseUpdated(m_unObjectId, GetPose(), sizeof(DriverPose_t));
        }
    }

    std::string GetSerialNumber() const { return m_sSerialNumber; }

private:
    OvrController* m_leftController;
    OvrController* m_rightController;
    
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
class CServerDriver_Sample : public IServerTrackedDeviceProvider {
public:
    CServerDriver_Sample()
            : m_pNullHmdLatest(nullptr), m_bEnableNullDriver(true) {
    }

    EVRInitError Init(vr::IVRDriverContext *pDriverContext) override {
        VR_INIT_SERVER_DRIVER_CONTEXT(pDriverContext);
        InitDriverLog(vr::VRDriverLog());

        m_pNullHmdLatest = new CSampleDeviceDriver();

        DriverLog(": Add device: %s\n", m_pNullHmdLatest->GetSerialNumber().c_str());

        vr::VRServerDriverHost()->TrackedDeviceAdded(
                m_pNullHmdLatest->GetSerialNumber().c_str(),
                vr::TrackedDeviceClass_HMD,
                m_pNullHmdLatest
        );
        return VRInitError_None;
    };

    void Cleanup() override {
        threadState->destroy();
        CleanupDriverLog();
        delete m_pNullHmdLatest;
        m_pNullHmdLatest = nullptr;
    };

    const char *const *GetInterfaceVersions() override { return vr::k_InterfaceVersions; }

    void RunFrame() override {
        if (m_pNullHmdLatest) {
            m_pNullHmdLatest->RunFrame();
        }
    };

    bool ShouldBlockStandbyMode() override { return false; }

    void EnterStandby() override {}

    void LeaveStandby() override {}

private:
    CSampleDeviceDriver *m_pNullHmdLatest;

    bool m_bEnableNullDriver;
};

CServerDriver_Sample g_serverDriverNull;
CWatchdogDriver_Sample g_watchdogDriverNull;

//-----------------------------------------------------------------------------
// Purpose:
//-----------------------------------------------------------------------------
HMD_DLL_EXPORT void *HmdDriverFactory(const char *pInterfaceName, int *pReturnCode) {
    if (0 == strcmp(IServerTrackedDeviceProvider_Version, pInterfaceName)) {
        return &g_serverDriverNull;
    }
    if (0 == strcmp(IVRWatchdogProvider_Version, pInterfaceName)) {
        return &g_watchdogDriverNull;
    }

    if (pReturnCode)
        *pReturnCode = VRInitError_Init_InterfaceNotFound;

    return nullptr;
}
