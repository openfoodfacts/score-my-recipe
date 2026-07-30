"""Validate that the JSON schema examples declared in ``api.types`` actually
instantiate the model they document.

For every Pydantic model in :mod:`api.types` that ships an ``examples`` entry
through ``model_config.json_schema_extra``, we build an instance from each
example. A failing example means the documentation drifted from the actual
model definition, which is usually a bug.

The parametrization is computed at module load time by introspecting
:mod:`api.types`, so new models with examples are picked up automatically.
"""

import inspect

import pytest
from pydantic import BaseModel

from api import types


def _models_with_examples():
    """Collect ``(model, example)`` pairs from every BaseModel in ``api.types``.

    A model is only relevant when its own ``model_config`` declares a
    non-empty ``examples`` list through ``json_schema_extra``. We read the
    config straight from the class (rather than the merged JSON schema) so a
    subclass is only tested against the examples it explicitly declares,
    never against examples inherited from a parent.
    """
    pairs = []
    num_classes = 0
    for _, obj in inspect.getmembers(types, inspect.isclass):
        if not issubclass(obj, BaseModel) or obj is BaseModel:
            continue
        num_classes += 1
        # ``model_config`` is a ConfigDict merged with the parents', but the
        # ``json_schema_extra`` key is replaced (not deep-merged) by the
        # subclass when it redefines it, so the value seen here is the one
        # the class actually declares.
        schema_extra = obj.model_config.get("json_schema_extra")
        if not isinstance(schema_extra, dict):
            continue
        examples = schema_extra.get("examples")
        if not examples:
            continue

        for index, example in enumerate(examples):
            pairs.append(
                pytest.param(obj, example, id=f"{obj.__name__}-{index}")
            )
    # we want at least 50% of the models to have examples
    if len(pairs) < num_classes / 2:
        raise RuntimeError(
            f"Not enough models with examples found in api.types ({len(pairs)}/{num_classes}). "
            "Expecting at least 50% of the models to have examples. "
        )
    return pairs


@pytest.mark.parametrize("model_cls, example", _models_with_examples())
def test_example_instantiates_model(model_cls, example):
    """Each documented example must be accepted by the model constructor."""
    instance = model_cls.model_validate(example)
    assert isinstance(instance, model_cls)
