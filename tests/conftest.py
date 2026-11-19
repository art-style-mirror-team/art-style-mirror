"""pytest 공통 설정.

- 저장소 루트를 import 경로에 넣어 `import app`, `from modules import ...`가 되게 한다.
- 실제 모델(CLIP 등)을 쓰는 테스트는 `@pytest.mark.model`로 표시하고 기본으로 건너뛴다.
  표시가 없는 테스트에서는 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼워, 형식 검사가
  모델 다운로드 없이 몇 초 안에 끝나게 한다.
- 실제 모델까지 돌리려면: `pytest --run-model` 또는 환경 변수 `RUN_MODEL_TESTS=1`.

가짜로 바꿔 끼우려면 다른 모듈은 모델 함수를 `data.embed_image(...)`처럼 모듈을 통해 불러야 한다.
`from modules.data import embed_image`로 가져오면 바꿔 끼울 수 없다.
"""

import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.fakes import FAKES


def _run_model(config: pytest.Config) -> bool:
    return bool(config.getoption("--run-model")) or os.environ.get("RUN_MODEL_TESTS") == "1"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-model",
        action="store_true",
        default=False,
        help="실제 모델을 내려받거나 불러오는 테스트(@pytest.mark.model)도 실행한다",
    )


def pytest_configure(config: pytest.Config) -> None:
    if not _run_model(config):
        # 실수로 모델을 내려받으려 하면 오래 기다리지 않고 바로 실패하게 한다.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _run_model(config):
        return
    skip = pytest.mark.skip(reason="실제 모델 테스트: --run-model 또는 RUN_MODEL_TESTS=1로 실행")
    for item in items:
        if "model" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _fake_models(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """`model` 표시가 없는 테스트에서는 모델 함수를 가짜로 바꿔 끼운다."""
    if request.node.get_closest_marker("model"):
        return
    for module_path, funcs in FAKES.items():
        module = importlib.import_module(module_path)
        for name, fake in funcs.items():
            monkeypatch.setattr(module, name, fake)
