from typing import Any, Dict, List, Literal, Optional, Type, Union

import supervision as sv
from pydantic import AliasChoices, ConfigDict, Field

from inference.core.entities.requests.doctr import DoctrOCRInferenceRequest
from inference.core.env import (
    HOSTED_CORE_MODEL_URL,
    LOCAL_INFERENCE_API_URL,
    WORKFLOWS_REMOTE_API_TARGET,
    WORKFLOWS_REMOTE_EXECUTION_MAX_STEP_BATCH_SIZE,
    WORKFLOWS_REMOTE_EXECUTION_MAX_STEP_CONCURRENT_REQUESTS,
)
from inference.core.managers.base import ModelManager
from inference.core.workflows.constants import (
    PARENT_ID_KEY,
    PREDICTION_TYPE_KEY,
    ROOT_PARENT_ID_KEY,
)
from inference.core.workflows.core_steps.common.utils import (
    attach_parent_info,
    attach_prediction_type_info,
    convert_to_sv_detections,
    load_core_model,
)
from inference.core.workflows.entities.base import (
    Batch,
    OutputDefinition,
    WorkflowImageData,
)
from inference.core.workflows.entities.types import (
    BATCH_OF_PARENT_ID_KIND,
    BATCH_OF_PREDICTION_TYPE_KIND,
    BATCH_OF_STRING_KIND,
    StepOutputImageSelector,
    WorkflowImageSelector,
)
from inference.core.workflows.prototypes.block import (
    WorkflowBlock,
    WorkflowBlockManifest,
)
from inference_sdk import InferenceConfiguration, InferenceHTTPClient

LONG_DESCRIPTION = """
 Retrieve the characters in an image using Optical Character Recognition (OCR).

This block returns the text within an image.

You may want to use this block in combination with a detections-based block (i.e. 
ObjectDetectionBlock). An object detection model could isolate specific regions from an 
image (i.e. a shipping container ID in a logistics use case) for further processing. 
You can then use a CropBlock to crop the region of interest before running OCR.

Using a detections model then cropping detections allows you to isolate your analysis 
on particular regions of an image.
"""


class BlockManifest(WorkflowBlockManifest):
    model_config = ConfigDict(
        json_schema_extra={
            "short_description": "Run Optical Character Recognition on a model.",
            "long_description": LONG_DESCRIPTION,
            "license": "Apache-2.0",
            "block_type": "model",
        }
    )
    type: Literal["OCRModel"]
    name: str = Field(description="Unique name of step in workflows")
    images: Union[WorkflowImageSelector, StepOutputImageSelector] = Field(
        description="Reference at image to be used as input for step processing",
        examples=["$inputs.image", "$steps.cropping.crops"],
        validation_alias=AliasChoices("images", "image"),
    )

    @classmethod
    def describe_outputs(cls) -> List[OutputDefinition]:
        return [
            OutputDefinition(name="result", kind=[BATCH_OF_STRING_KIND]),
            OutputDefinition(name="parent_id", kind=[BATCH_OF_PARENT_ID_KIND]),
        ]


class OCRModelBlock(WorkflowBlock):
    # TODO: we need data model for OCR predictions

    def __init__(
        self,
        model_manager: ModelManager,
        api_key: Optional[str],
    ):
        self._model_manager = model_manager
        self._api_key = api_key

    @classmethod
    def get_init_parameters(cls) -> List[str]:
        return ["model_manager", "api_key"]

    @classmethod
    def get_manifest(cls) -> Type[WorkflowBlockManifest]:
        return BlockManifest

    async def run_locally(
        self,
        images: Batch[Optional[WorkflowImageData]],
    ) -> List[Dict[str, Union[sv.Detections, Any]]]:
        predictions = []
        non_empty_images = [i for i in images.iter_nonempty()]
        for single_image in non_empty_images:
            inference_request = DoctrOCRInferenceRequest(
                image=single_image.numpy_image,
                api_key=self._api_key,
            )
            doctr_model_id = load_core_model(
                model_manager=self._model_manager,
                inference_request=inference_request,
                core_model="doctr",
            )
            result = await self._model_manager.infer_from_request(
                doctr_model_id, inference_request
            )
            predictions.append(result.model_dump())
        results = self._post_process_result(
            predictions=predictions,
            images=non_empty_images,
        )
        return images.align_batch_results(
            results=results,
            null_element={
                PARENT_ID_KEY: None,
                ROOT_PARENT_ID_KEY: None,
                "result": None,
            },
        )

    async def run_remotely(
        self,
        images: Batch[Optional[WorkflowImageData]],
    ) -> List[Dict[str, Union[sv.Detections, Any]]]:
        api_url = (
            LOCAL_INFERENCE_API_URL
            if WORKFLOWS_REMOTE_API_TARGET != "hosted"
            else HOSTED_CORE_MODEL_URL
        )
        client = InferenceHTTPClient(
            api_url=api_url,
            api_key=self._api_key,
        )
        if WORKFLOWS_REMOTE_API_TARGET == "hosted":
            client.select_api_v0()
        configuration = InferenceConfiguration(
            max_batch_size=WORKFLOWS_REMOTE_EXECUTION_MAX_STEP_BATCH_SIZE,
            max_concurrent_requests=WORKFLOWS_REMOTE_EXECUTION_MAX_STEP_CONCURRENT_REQUESTS,
        )
        client.configure(configuration)
        non_empty_images = [i for i in images.iter_nonempty()]
        non_empty_inference_images = [i.numpy_image for i in non_empty_images]
        predictions = await client.ocr_image_async(
            inference_input=non_empty_inference_images,
        )
        if len(images) == 1:
            predictions = [predictions]
        results = self._post_process_result(
            predictions=predictions,
            images=non_empty_images,
        )
        return images.align_batch_results(
            results=results,
            null_element={
                PARENT_ID_KEY: None,
                ROOT_PARENT_ID_KEY: None,
                "result": None,
            },
        )

    def _post_process_result(
        self,
        images: List[WorkflowImageData],
        predictions: List[dict],
    ) -> List[Dict[str, Union[sv.Detections, Any]]]:
        for prediction, image in zip(predictions, images):
            prediction[PREDICTION_TYPE_KEY] = "ocr"
            predictions[PARENT_ID_KEY] = image.parent_metadata.parent_id
            predictions[ROOT_PARENT_ID_KEY] = (
                image.workflow_root_ancestor_metadata.parent_id
            )
        return predictions
