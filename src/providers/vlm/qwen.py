import importlib.util
import threading
from pathlib import Path
from typing import Any

from src.core.exceptions import ProcessingError, ProviderUnavailableError
from src.providers.base import ProviderResult


class QwenVLProvider:
    name = "qwen2.5-vl"

    def __init__(self, model_id: str) -> None:
        self._model_id = model_id
        self._model: Any = None
        self._processor: Any = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        return all(
            importlib.util.find_spec(name) for name in ("torch", "transformers", "qwen_vl_utils")
        )

    def _load(self) -> tuple[Any, Any]:
        if not self.is_available():
            raise ProviderUnavailableError("Qwen VLM optional dependencies are not installed")
        with self._lock:
            if self._model is None:
                from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

                self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self._model_id, torch_dtype="auto", device_map="auto"
                )
                self._processor = AutoProcessor.from_pretrained(self._model_id)
        return self._model, self._processor

    def extract(self, document: Path) -> ProviderResult:
        if document.suffix.lower() == ".pdf":
            raise ProcessingError("Qwen VLM requires rasterized PDF pages")
        try:
            from qwen_vl_utils import process_vision_info

            model, processor = self._load()
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": document.as_uri()},
                        {
                            "type": "text",
                            "text": "Transcribe this document exactly. Return text only.",
                        },
                    ],
                }
            ]
            prompt = processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            images, videos = process_vision_info(messages)
            inputs = processor(
                text=[prompt], images=images, videos=videos, padding=True, return_tensors="pt"
            ).to(model.device)
            generated = model.generate(**inputs, max_new_tokens=2048)
            trimmed = [
                output[len(source) :]
                for source, output in zip(inputs.input_ids, generated, strict=True)
            ]
            text = processor.batch_decode(trimmed, skip_special_tokens=True)[0].strip()
            return ProviderResult(text=text, confidence=0.9 if text else 0, provider=self.name)
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProcessingError(f"Qwen VLM failed: {exc}") from exc
