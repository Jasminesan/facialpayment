import cv2
import numpy as np
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(current_dir, "../models")

try:
    import depthai as dai
    HAS_DEPTHAI = True
except ImportError:
    HAS_DEPTHAI = False
    print("⚠️ Warning: 'depthai' library not found. OAK-D features disabled.")

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
from config.settings import Config

class CameraService(QThread):
    frame_received = Signal(QImage)
    face_detected = Signal(list)

    def __init__(self, send_interval=2.0):
        super().__init__()
        self.running = False
        self.mock_mode = Config.IS_DEV
        self.send_interval = send_interval
        self.last_det_bbox = None 
        
        self.fd_blob = os.path.join(MODEL_DIR, "face-detection.blob")
        self.fr_blob = os.path.join(MODEL_DIR, "face-recognition.blob")
        
        if not self.mock_mode and (not os.path.exists(self.fd_blob) or not os.path.exists(self.fr_blob)):
            print("❌ Error: Model files not found! Falling back to Mock mode.")
            self.mock_mode = True 

    def run(self):
        self.running = True
        print(f"📷 Camera Service Started (Interval: {self.send_interval}s)")

        if self.mock_mode or not HAS_DEPTHAI:
            self._run_mock_camera()
        else:
            try:
                self._run_oak_pipeline()
            except Exception as e:
                print(f"❌ OAK-D Error: {e}")
                print("⚠️ Switching to Mock Mode...")
                self.mock_mode = True
                self._run_mock_camera()

    def _run_mock_camera(self):
        print("📷 Running in MOCK MODE (Webcam)")
        cap = cv2.VideoCapture(0)
        last_scan_time = time.time()

        while self.running:
            ret, frame = cap.read()
            if ret:
                self._emit_frame(frame)
                if time.time() - last_scan_time > self.send_interval:
                    # Mock vector length 256
                    mock_vector = [0.5] * 256 
                    self.face_detected.emit(mock_vector)
                    last_scan_time = time.time()
            self.msleep(30)
        cap.release()

    def _run_oak_pipeline(self):
        print("📷 Running in OAK-D MODE (Intel Model 0095)")
        pipeline = dai.Pipeline()

        # 1. Color Camera
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        cam_rgb.setPreviewSize(300, 300)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam_rgb.setFps(30)

        # 2. Face Detection
        face_det = pipeline.create(dai.node.MobileNetDetectionNetwork)
        face_det.setConfidenceThreshold(0.4)
        face_det.setBlobPath(self.fd_blob)
        cam_rgb.preview.link(face_det.input)

        # 3. Script Node
        script = pipeline.create(dai.node.Script)
        script.setScript("""
            while True:
                img = node.io['preview'].get()
                face_dets = node.io['face_det_in'].get()
                
                if len(face_dets.detections) > 0:
                    det = face_dets.detections[0]
                    
                    # Fix crop size
                    width = det.xmax - det.xmin
                    height = det.ymax - det.ymin
                    
                    # Expand a bit
                    new_w = width * 1.1
                    new_h = height * 1.1
                    cx = det.xmin + width / 2
                    cy = det.ymin + height / 2
                    
                    xmin = max(0, cx - new_w / 2)
                    ymin = max(0, cy - new_h / 2)
                    xmax = min(1, cx + new_w / 2)
                    ymax = min(1, cy + new_h / 2)

                    cfg = ImageManipConfig()
                    cfg.setCropRect(xmin, ymin, xmax, ymax)
                    # ✅ ปรับขนาดเป็น 128x128 ตามโมเดล Intel
                    cfg.setResize(128, 128) 
                    cfg.setKeepAspectRatio(False)
                    
                    node.io['manip_cfg'].send(cfg)
                    node.io['manip_img'].send(img)
        """)
        face_det.out.link(script.inputs['face_det_in'])
        cam_rgb.preview.link(script.inputs['preview'])

        # 4. ImageManip
        manip = pipeline.create(dai.node.ImageManip)
        # ✅ ปรับขนาดเป็น 128x128
        manip.initialConfig.setResize(128, 128)
        manip.inputConfig.setWaitForMessage(True)
        script.outputs['manip_cfg'].link(manip.inputConfig)
        script.outputs['manip_img'].link(manip.inputImage)

        # 5. Face Recognition
        face_rec = pipeline.create(dai.node.NeuralNetwork)
        face_rec.setBlobPath(self.fr_blob)
        manip.out.link(face_rec.input)

        # Outputs
        xout_rgb = pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.video.link(xout_rgb.input)

        xout_rec = pipeline.create(dai.node.XLinkOut)
        xout_rec.setStreamName("rec")
        face_rec.out.link(xout_rec.input)
        
        xout_det = pipeline.create(dai.node.XLinkOut)
        xout_det.setStreamName("det")
        face_det.out.link(xout_det.input)

        with dai.Device(pipeline) as device:
            print("✅ OAK-D AI Pipeline Started! (Intel Model)")
            q_rgb = device.getOutputQueue("rgb", 4, False)
            q_rec = device.getOutputQueue("rec", 4, False)
            q_det = device.getOutputQueue("det", 4, False)

            last_rec_time = time.time()
            self.last_det_bbox = None

            while self.running:
                in_rgb = q_rgb.tryGet()
                if in_rgb:
                    frame = in_rgb.getCvFrame()
                    if self.last_det_bbox:
                        h, w = frame.shape[:2]
                        x1, y1, x2, y2 = self.last_det_bbox
                        cv2.rectangle(frame, (int(x1*w), int(y1*h)), (int(x2*w), int(y2*h)), (0, 255, 0), 2)
                    frame_small = cv2.resize(frame, (700, 700))
                    self._emit_frame(frame_small)

                in_det = q_det.tryGet()
                if in_det:
                    dets = in_det.detections
                    if len(dets) > 0:
                        d = dets[0]
                        self.last_det_bbox = (d.xmin, d.ymin, d.xmax, d.ymax)
                    else:
                        self.last_det_bbox = None

                in_rec = q_rec.tryGet()
                if in_rec:
                    if time.time() - last_rec_time > self.send_interval:
                        vector = in_rec.getFirstLayerFp16()
                        if len(vector) == 256:
                            print(f"✅ VECTOR ARRIVED! (Len: {len(vector)})")
                            self.face_detected.emit(vector)
                            last_rec_time = time.time()
                
                self.msleep(5)

    def _emit_frame(self, frame):
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        qt_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.frame_received.emit(qt_img)

    def stop(self):
        self.running = False
        self.wait()