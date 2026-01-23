import depthai as dai
import cv2

# Create pipeline
pipeline = dai.Pipeline()
cam = pipeline.create(dai.node.ColorCamera)
cam.setPreviewSize(300, 300)
xout = pipeline.create(dai.node.XLinkOut)
xout.setStreamName("preview")
cam.preview.link(xout.input)

# Connect to device
try:
    with dai.Device(pipeline) as device:
        q = device.getOutputQueue(name="preview")
        print("OAK-D Connected! Press 'q' to exit.")
        while True:
            frame = q.get().getCvFrame()
            cv2.imshow("OAK-D Test", frame)
            if cv2.waitKey(1) == ord('q'):
                break
except Exception as e:
    print(f"Failed to connect OAK-D: {e}")