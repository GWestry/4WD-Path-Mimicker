4WD-Path-Mimicker
11/5/2025- Added green object detection using the Freenove Car Camera and OpenCV to process images. Images can be detected while car is moving retaining full motor control logic functionality. Resolution was dropped since color detection is overall simple and so the CPU isn't clogged ensuring smooth movement/control.


Full stack development program for a Freenove 4WD Smart Car. User can draw path on web browser and car will drive that path on the ground.
Program is run through a Flask server and controls a Raspberry Pi and sends coordinates through OpenCV.
Raspberry Pi is connected to the Freenove 4WD Smart Car and controls its motors through GPIO.

Video demonstration of car motor logic: https://youtube.com/shorts/_DpPmxC0tnw?feature=share
Video demonstration of green object detection: https://youtube.com/shorts/l8elxHz6diM?feature=share
