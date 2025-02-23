"""
This is just example, test implementation, please do not assume it being fully functional.
"""

from copy import deepcopy
from typing import Dict, List, Literal, Optional, Type, Union

import numpy as np
import supervision as sv
from pydantic import ConfigDict, Field

from inference.core.workflows.execution_engine.entities.base import (
    Batch,
    OutputDefinition,
    WorkflowImageData,
)
from inference.core.workflows.execution_engine.entities.types import (
    BATCH_OF_INSTANCE_SEGMENTATION_PREDICTION_KIND,
    BATCH_OF_KEYPOINT_DETECTION_PREDICTION_KIND,
    BATCH_OF_OBJECT_DETECTION_PREDICTION_KIND,
    StepOutputImageSelector,
    StepOutputSelector,
    WorkflowImageSelector,
)
from inference.core.workflows.prototypes.block import (
    BlockResult,
    WorkflowBlock,
    WorkflowBlockManifest,
)


class BlockManifest(WorkflowBlockManifest):
    model_config = ConfigDict(
        json_schema_extra={
            "short_description": "",
            "long_description": "",
            "license": "Apache-2.0",
            "block_type": "transformation",
        }
    )
    type: Literal["DetectionsToParentsCoordinatesNonBatch"]
    image: Union[WorkflowImageSelector, StepOutputImageSelector] = Field(
        description="Reference an image to be used as input for step processing",
        examples=["$inputs.image", "$steps.cropping.crops"],
    )
    image_predictions: StepOutputSelector(
        kind=[
            BATCH_OF_OBJECT_DETECTION_PREDICTION_KIND,
            BATCH_OF_INSTANCE_SEGMENTATION_PREDICTION_KIND,
            BATCH_OF_KEYPOINT_DETECTION_PREDICTION_KIND,
        ]
    ) = Field(
        description="Reference to predictions of detection-like model, that can be based of cropping "
        "(detection must define RoI - eg: bounding box)",
        examples=["$steps.my_object_detection_model.predictions"],
    )

    @classmethod
    def get_input_dimensionality_offsets(
        cls,
    ) -> Dict[str, int]:
        return {
            "image": 0,
            "image_predictions": 1,
        }

    @classmethod
    def get_dimensionality_reference_property(cls) -> Optional[str]:
        return "image_predictions"

    @classmethod
    def describe_outputs(cls) -> List[OutputDefinition]:
        return [
            OutputDefinition(
                name="predictions",
                kind=[
                    BATCH_OF_OBJECT_DETECTION_PREDICTION_KIND,
                    BATCH_OF_INSTANCE_SEGMENTATION_PREDICTION_KIND,
                    BATCH_OF_KEYPOINT_DETECTION_PREDICTION_KIND,
                ],
            ),
        ]


class DetectionsToParentCoordinatesNonBatchBlock(WorkflowBlock):

    @classmethod
    def get_manifest(cls) -> Type[WorkflowBlockManifest]:
        return BlockManifest

    def run(
        self,
        image: WorkflowImageData,
        image_predictions: Batch[sv.Detections],
    ) -> BlockResult:
        parent_id = image.parent_metadata.parent_id
        parent_coordinates = image.parent_metadata.origin_coordinates
        transformed_predictions = []
        for prediction in image_predictions:
            prediction_copy = deepcopy(prediction)
            prediction_copy["parent_id"] = np.array([parent_id] * len(prediction))
            if parent_coordinates:
                offset = [0, 0]
                dimensions = [
                    parent_coordinates.origin_height,
                    parent_coordinates.origin_width,
                ]
                prediction_copy["parent_coordinates"] = np.array(
                    [offset] * len(prediction)
                )
                prediction_copy["parent_dimensions"] = np.array(
                    [dimensions] * len(prediction)
                )
            transformed_predictions.append({"predictions": prediction_copy})
        return transformed_predictions
