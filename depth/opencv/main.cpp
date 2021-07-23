// Standard library headers
#include <iostream>
#include <stdio.h>

// OpenCV headers
#include <opencv2/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc.hpp> // cv::resize()
#include <opencv2/videoio.hpp>
#include <opencv2/calib3d.hpp> // cv::undistort()

#include <opencv2/core/version.hpp>
#if CV_MAJOR_VERSION >= 3
#include <opencv2/imgcodecs.hpp>
#endif

// VPI headers
#include <vpi/OpenCVInterop.hpp>

#include <vpi/Image.h>
#include <vpi/Status.h>
#include <vpi/Stream.h>
#include <vpi/algo/StereoDisparity.h>

#define CHECK_STATUS(STMT)                                    \
    do {                                                      \
        VPIStatus status = (STMT);                            \
        if (status != VPI_SUCCESS) {                          \
            char buffer[VPI_MAX_STATUS_MESSAGE_LENGTH];       \
            vpiGetLastStatusMessage(buffer, sizeof(buffer));  \
            std::ostringstream ss;                            \
            ss << vpiStatusGetName(status) << ": " << buffer; \
            throw std::runtime_error(ss.str());               \
        }                                                     \
    } while (0);

std::string gstreamer_pipeline(int sensor_id, int capture_width,
    int capture_height, int display_width,
    int display_height, int framerate,
    int flip_method)
{
    return "nvarguscamerasrc sensor_id=" + std::to_string(sensor_id) + " ! video/x-raw(memory:NVMM), width=(int)" + std::to_string(capture_width) + ", height=(int)" + std::to_string(capture_height) + ", format=(string)NV12, framerate=(fraction)" + std::to_string(framerate) + "/1 ! nvvidconv flip-method=" + std::to_string(flip_method) + " ! video/x-raw, width=(int)" + std::to_string(display_width) + ", height=(int)" + std::to_string(display_height) + ", format=(string)BGRx ! videoconvert ! video/x-raw, "
                                                                                                                                                                                                                                                                                                                                                                                                                                                                      "format=(string)BGR ! appsink max-buffers=1 drop=true";
}

int main()
{

    // Gstreamer capture parameters
    int CAP_W = 1920;
    int CAP_H = 1080;
    int DISP_W = 1920;
    int DISP_H = 1080;
    int VPI_W = 480;
    int VPI_H = 270;

    int FPS = 30;
    int FLIP_METHOD = 2;

    // OpenCV image containers
    cv::Mat img_l_3ch, img_r_3ch, img_l, img_r, img_r_rect, img_l_rect, img_r_rect_small, img_l_rect_small;

    // remap() parameters
    cv::Mat map_l_x, map_l_y, map_r_x, map_r_y;

    std::cout << "Loading rectification params..." << std::endl; 
    cv::FileStorage fs("remap_rectify_params.yml", cv::FileStorage::READ);
    fs["map_l_x"] >> map_l_x;
    fs["map_l_y"] >> map_l_y;
    fs["map_r_x"] >> map_r_x;
    fs["map_r_y"] >> map_r_y;
    fs.release();
    std::cout << "Rectification params loaded." << std::endl;
    
    // VPI containers
    VPIImage img_vpi_l = NULL;
    VPIImage img_vpi_r = NULL;
    VPIImage disparity = NULL; // CV_16UC1, VPI_IMAGE_FORMAT_U16
    VPIStream stream = NULL;

    VPIStereoDisparityEstimatorParams disp_params;
    disp_params.windowSize = 5;
    disp_params.maxDisparity = 64;

    // Pick the backend
    VPIBackend backend;
    backend = VPI_BACKEND_PVA;
    // backend = VPI_BACKEND_CPU;
    // backend = VPI_BACKEND_CUDA;

    VPIPayload stereo = NULL;

    // Setting parameters for StereoSGBM algorithm
    int minDisparity = 0;
    int numDisparities = 64;
    int blockSize = 16;
    int disp12MaxDiff = 1;
    int uniquenessRatio = 20;
    int speckleWindowSize = 10;
    int speckleRange = 8;

    // Creating an object of StereoSGBM algorithm
    cv::Ptr<cv::StereoSGBM> stereoSGBM = cv::StereoSGBM::create(minDisparity,numDisparities,blockSize,
    disp12MaxDiff,uniquenessRatio,speckleWindowSize,speckleRange);

    // Calculating disparith using the StereoSGBM algorithm
    cv::Mat disp;
    

    CHECK_STATUS(vpiCreateStereoDisparityEstimator(
        backend, VPI_W, VPI_H, VPI_IMAGE_FORMAT_U16, NULL, &stereo));

    std::string pipeline_right = gstreamer_pipeline(1, CAP_W, CAP_H, DISP_W, DISP_H, FPS, FLIP_METHOD);
    std::string pipeline_left = gstreamer_pipeline(0, CAP_W, CAP_H, DISP_W, DISP_H, FPS, FLIP_METHOD);

    cv::VideoCapture cap_l(pipeline_left, cv::CAP_GSTREAMER);
    cv::VideoCapture cap_r(pipeline_right, cv::CAP_GSTREAMER);

    if (!cap_l.isOpened() || !cap_r.isOpened()) {
        std::cerr << "Failed to open camera." << std::endl;
        return (-1);
    }

    // X server windows
    cv::namedWindow("left", cv::WINDOW_AUTOSIZE);
    cv::namedWindow("right", cv::WINDOW_AUTOSIZE);
    cv::moveWindow("left", 0, 0); // move RGB window to upper-left corner
    cv::moveWindow("right", VPI_W, 0); // Align windows side by side

    int retval = 0;

    // Create the stream for the given backend.
    CHECK_STATUS(vpiStreamCreate(backend, &stream));

    // Create the image where the disparity map will be stored.
    CHECK_STATUS(vpiImageCreate(VPI_W, VPI_H, VPI_IMAGE_FORMAT_U16, 0, &disparity));


    std::vector<float> distortion_coef_right = {-0.36810567,  0.22406853, -0.00049262, -0.00003734, -0.1056876 };
    std::vector<float> distortion_coef_left = {-0.37090124,  0.2319178 , -0.00026621, -0.00059378, -0.11590811 };


    std::vector<float> intriniscs_right = {
        1562.8844672 ,    0.        , 1003.36066189,
        0.        , 1558.88689229,  448.76868195,
        0.        ,    0.        ,    1.        };

    std::vector<float> intrinsics_left = {
        1572.21759392,    0.        ,  921.46909424,
        0.        , 1568.02105297,  437.08755814,
        0.        ,    0.        ,    1.        
    };

    cv::Mat dist_coeff_l = cv::Mat(1, 5, CV_32F, &distortion_coef_left[0]);
    cv::Mat K_l = cv::Mat(3, 3, CV_32F, &intrinsics_left[0]);

    cv::Mat dist_coeff_r = cv::Mat(1, 5, CV_32F, &distortion_coef_right[0]);
    cv::Mat K_r = cv::Mat(3, 3, CV_32F, &intriniscs_right[0]);

    while (true) {
        bool retv_l = cap_l.read(img_l_3ch);
        bool retv_r = cap_r.read(img_r_3ch);

        if (!retv_l || !retv_r) {
            std::cerr << "capture error" << std::endl;
            break;
        }

        // 3ch -> 1ch
        cv::cvtColor(img_l_3ch, img_l, cv::COLOR_BGR2GRAY);
        cv::cvtColor(img_r_3ch, img_r, cv::COLOR_BGR2GRAY);

        auto start = std::chrono::steady_clock::now();

        cv::remap(img_l, img_l_rect, map_l_x, map_l_y, cv::INTER_LANCZOS4, cv::BORDER_CONSTANT, 0);
        cv::remap(img_r, img_r_rect, map_r_x, map_r_y, cv::INTER_LANCZOS4, cv::BORDER_CONSTANT, 0);

        auto end = std::chrono::steady_clock::now();
        cv::resize(img_l_rect, img_l_rect, cv::Size(480,270));
        cv::resize(img_r_rect, img_r_rect, cv::Size(480,270));


        stereoSGBM->compute(img_l_rect, img_r_rect, disp);
        std::cout << "Unwarp time in milliseconds: "
        << std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()
        << " ms" << std::endl;

        // Normalizing the disparity map for better visualisation 
        cv::normalize(disp, disp, 0, 255, cv::NORM_MINMAX, CV_8UC1);
        applyColorMap(disp, disp, cv::COLORMAP_JET);

        // // Displaying the disparity map
        cv::imshow("disparity OpenCV",disp);
        // cv::imshow("img_l_3ch", img_l_3ch);

        int keycode = cv::waitKey(1) & 0xff;
        if (keycode == 27)
            break;
        



        // auto end = std::chrono::steady_clock::now();

        // std::cout << "Unwarp time in milliseconds: "
        // << std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()
        // << " ms" << std::endl;

        // // uint8 -> uint16
        // img_l_rect.convertTo(img_l_rect, CV_16UC1);
        // img_r_rect.convertTo(img_r_rect, CV_16UC1);

        // // OpenCV->VPI wrapper
        // CHECK_STATUS(vpiImageCreateOpenCVMatWrapper(img_l_rect, 0, &img_vpi_l));
        // CHECK_STATUS(vpiImageCreateOpenCVMatWrapper(img_r_rect, 0, &img_vpi_r));

        // // Submit it with the input and output images

        // CHECK_STATUS(vpiSubmitStereoDisparityEstimator(
        //     stream, backend, stereo, img_vpi_l, img_vpi_r, disparity, NULL,
        //     &disp_params));

        // // Wait until the algorithm finishes processing
        // CHECK_STATUS(vpiStreamSync(stream)); // TODO: needed?

        // // Lock output to retrieve its data on cpu memory
        // VPIImageData buff;
        // CHECK_STATUS(vpiImageLock(disparity, VPI_LOCK_READ, &buff));

        // // Make an OpenCV matrix out of this image
        // cv::Mat cvOut(buff.planes[0].height, buff.planes[0].width, CV_16UC1,
        //     buff.planes[0].data, buff.planes[0].pitchBytes);

        // // Scale result and write it to disk
        // double min, max;
        // minMaxLoc(cvOut, &min, &max);
        // cvOut.convertTo(cvOut, CV_8UC1, 255.0 / (max - min), -min);

        // // Done handling output, don't forget to unlock it.
        // CHECK_STATUS(vpiImageUnlock(disparity));


        // cv::blur(cvOut, cvOut, cv::Size(5,5));
        // minMaxLoc(img_l_rect, &min, &max);
        // img_l_rect.convertTo(img_l_rect, CV_8UC1, 255.0 / (max - min), -min);
        // img_r_rect.convertTo(img_r_rect, CV_8UC1, 255.0 / (max - min), -min);

        cv::imshow("left", img_l_rect);
        cv::imshow("right", img_r_rect);
        // cv::imshow("disparity", cvOut);

    }
    // Cleanup

    // Make sure stream is synchronized before destroying the objects
    // that might still be in use.
    if (stream != NULL) {
        vpiStreamSync(stream);
    }

    vpiImageDestroy(img_vpi_l);
    vpiImageDestroy(img_vpi_r);
    vpiImageDestroy(disparity);
    vpiPayloadDestroy(stereo);
    vpiStreamDestroy(stream);

    cap_l.release();
    cap_r.release();

    cv::destroyAllWindows();
    return retval;
}
