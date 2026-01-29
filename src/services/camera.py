import cv2
import numpy as np
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(current_dir, "../models")

import depthai as dai


from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

class CameraService(QThread):
    frame_received = Signal(QImage)
    face_detected = Signal(list)

    def __init__(self, send_interval=2.0):
        super().__init__()
        self.running = False
        self.send_interval = send_interval
        self.last_det_bbox = None 
        
        self.fd_blob = os.path.join(MODEL_DIR, "face-detection.blob")
        self.fr_blob = os.path.join(MODEL_DIR, "face-recognition.blob")
        
        if not os.path.exists(self.fd_blob) or not os.path.exists(self.fr_blob):
            print(f"❌ Error: Model files not found in {MODEL_DIR}")
            self.running = False 

    def run(self):
        self.running = True
        print(f"📷 Camera Service Started (OAK-D Only) - Interval: {self.send_interval}s")

        try:
            self._run_oak_pipeline()
        except Exception as e:
            print(f"❌ OAK-D Critical Error: {e}")
            self.running = False

    def _run_oak_pipeline(self):
        print("📷 Initializing OAK-D Pipeline...")
        pipeline = dai.Pipeline()

        # 1. Setup Color Camera
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        cam_rgb.setPreviewSize(300, 300)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam_rgb.setFps(30)

        # 2. Setup Face Detection Network
        face_det = pipeline.create(dai.node.MobileNetDetectionNetwork)
        face_det.setConfidenceThreshold(0.5)
        face_det.setBlobPath(self.fd_blob)
        cam_rgb.preview.link(face_det.input)

        # 3. Setup Script Node (สำหรับ Crop หน้าคนจากภาพใหญ่)
        script = pipeline.create(dai.node.Script)
        script.setScript("""
            while True:
                img = node.io['preview'].get()
                face_dets = node.io['face_det_in'].get()
                
                if len(face_dets.detections) > 0:
                    det = face_dets.detections[0]
                    
                    # คำนวณขนาด Bounding Box
                    width = det.xmax - det.xmin
                    height = det.ymax - det.ymin
                    
                    # ขยายกรอบออกเล็กน้อย (10%)
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
                    # ✅ ปรับขนาดเป็น 128x128 สำหรับโมเดล Face Recognition
                    cfg.setResize(128, 128) 
                    cfg.setKeepAspectRatio(False)
                    
                    node.io['manip_cfg'].send(cfg)
                    node.io['manip_img'].send(img)
        """)
        face_det.out.link(script.inputs['face_det_in'])
        cam_rgb.preview.link(script.inputs['preview'])

        # 4. Setup ImageManip (รับคำสั่งจาก Script)
        manip = pipeline.create(dai.node.ImageManip)
        manip.initialConfig.setResize(128, 128)
        manip.inputConfig.setWaitForMessage(True)
        script.outputs['manip_cfg'].link(manip.inputConfig)
        script.outputs['manip_img'].link(manip.inputImage)

        # 5. Setup Face Recognition Network
        face_rec = pipeline.create(dai.node.NeuralNetwork)
        face_rec.setBlobPath(self.fr_blob)
        manip.out.link(face_rec.input)

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
            print("✅ OAK-D Connected & Pipeline Started!")
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
                            print(f"✅ Real Face Vector Detected! (Len: {len(vector)})")
                            self.face_detected.emit(vector) # ส่ง Vector จริงจาก OAK-D
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