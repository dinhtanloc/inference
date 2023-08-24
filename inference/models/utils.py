from inference.core.registries.roboflow import get_model_type
from inference.models.vit import VitClassification
from inference.models.yolact import YOLACT
from inference.models.yolov5 import YOLOv5InstanceSegmentation, YOLOv5ObjectDetection
from inference.models.yolov7 import YOLOv7InstanceSegmentation
from inference.models.yolov8 import (
    YOLOv8Classification,
    YOLOv8InstanceSegmentation,
    YOLOv8ObjectDetection,
)

ROBOFLOW_MODEL_TYPES = {
    ("classification", "vit"): VitClassification,
    ("classification", "yolov8n"): YOLOv8Classification,
    ("classification", "yolov8s"): YOLOv8Classification,
    ("classification", "yolov8m"): YOLOv8Classification,
    ("classification", "yolov8l"): YOLOv8Classification,
    ("classification", "yolov8x"): YOLOv8Classification,
    ("object-detection", "yolov5"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v2s"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v6n"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v6s"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v6m"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v6l"): YOLOv5ObjectDetection,
    ("object-detection", "yolov5v6x"): YOLOv5ObjectDetection,
    ("object-detection", "yolov8"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8s"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8n"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8s"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8m"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8l"): YOLOv8ObjectDetection,
    ("object-detection", "yolov8x"): YOLOv8ObjectDetection,
    (
        "instance-segmentation",
        "yolov5-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov5n-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov5s-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov5m-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov5l-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov5x-seg",
    ): YOLOv5InstanceSegmentation,
    (
        "instance-segmentation",
        "yolact",
    ): YOLACT,
    (
        "instance-segmentation",
        "yolov7-seg",
    ): YOLOv7InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8n",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8s",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8m",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8l",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8x",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8n-seg",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8s-seg",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8m-seg",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8l-seg",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8x-seg",
    ): YOLOv8InstanceSegmentation,
    (
        "instance-segmentation",
        "yolov8-seg",
    ): YOLOv8InstanceSegmentation,
}

try:
    from models.sam import SegmentAnything

    ROBOFLOW_MODEL_TYPES[("embed", "sam")] = SegmentAnything
except:
    pass

try:
    from inference.models.clip import Clip

    ROBOFLOW_MODEL_TYPES[("embed", "clip")] = Clip
except:
    pass


def get_roboflow_model(model_id, api_key=None, **kwargs):
    task, model = get_model_type(model_id, api_key=api_key)
    return ROBOFLOW_MODEL_TYPES[(task, model)](model_id, api_key=api_key, **kwargs)
