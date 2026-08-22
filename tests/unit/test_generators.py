import json

import pytest
from pydantic import JsonValue

from rci.generators import (
    GeneratorStatus,
    ManualGenerator,
    OpenAIDecodeStatus,
    OpenAIResponsesGenerator,
    QuestionInvocation,
    ScriptedGenerator,
    UnpersistedEffectError,
    decode_openai_response,
)


def invocation() -> QuestionInvocation:
    return QuestionInvocation(
        invocation_id="inv-1",
        contract_id="obligation-characterization",
        contract_version="1.0.0",
        scope_fingerprint="scope-fingerprint",
        binding_revision="binding-v1",
        referent_ids=("obligation-1",),
        rendered_question="What remains?",
        local_context=("payload is inert",),
        max_output_tokens=32,
    )


def test_manual_generator_never_invents_an_answer() -> None:
    result = ManualGenerator().generate(invocation())
    assert result.status is GeneratorStatus.NEEDS_MANUAL_INPUT
    assert result.payload is None


def test_scripted_generator_is_deterministic() -> None:
    generator = ScriptedGenerator({"inv-1": {"answer": "opaque"}})
    assert generator.generate(invocation()) == generator.generate(invocation())


def test_scripted_payload_is_deeply_snapshot_immutable() -> None:
    source: JsonValue = {"answer": ["first"]}
    generator = ScriptedGenerator({"inv-1": source})
    assert isinstance(source, dict)
    source_answer = source["answer"]
    assert isinstance(source_answer, list)
    source_answer.append("mutated-after-construction")
    result = generator.generate(invocation())
    assert result.payload == {"answer": ["first"]}
    assert isinstance(result.payload, dict)
    nested = result.payload["answer"]
    assert isinstance(nested, list)
    with pytest.raises(TypeError, match="frozen JSON"):
        nested.append("forbidden")


class _ClientThatMustNotRun:
    @property
    def responses(self) -> object:
        raise AssertionError("unpersisted generation touched the provider client")


def test_openai_direct_generation_fails_before_touching_client() -> None:
    generator = OpenAIResponsesGenerator(model="explicit-model", client=_ClientThatMustNotRun())
    with pytest.raises(UnpersistedEffectError, match="persisted"):
        generator.generate(invocation())


def test_openai_compilation_is_stateless_tool_free_and_bounded() -> None:
    request = OpenAIResponsesGenerator(model="explicit-model").compile(invocation())
    assert request.model == "explicit-model"
    assert request.input.endswith("Question:\nWhat remains?")
    assert request.tools == ()
    assert request.store is False
    assert request.max_output_tokens == 32


def test_openai_raw_decoder_records_status_usage_and_provisional_text() -> None:
    raw = json.dumps(
        {
            "id": "response-1",
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "opaque "},
                        {"type": "output_text", "text": "return"},
                    ],
                }
            ],
            "usage": {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6},
        },
        separators=(",", ":"),
    ).encode()

    decoded = decode_openai_response(raw)

    assert decoded.status is OpenAIDecodeStatus.DECODED
    assert decoded.summary is not None
    assert decoded.summary.execution_status == "completed"
    assert decoded.summary.output_text == "opaque return"
    assert dict(decoded.summary.usage) == {
        "input_tokens": 4,
        "output_tokens": 2,
        "total_tokens": 6,
    }


@pytest.mark.parametrize(
    ("raw", "status"),
    (
        (b"not-json", OpenAIDecodeStatus.MALFORMED),
        (b"[]", OpenAIDecodeStatus.UNSUPPORTED),
        (b'{"status":"completed","output":false}', OpenAIDecodeStatus.MALFORMED),
        (b'{"output":[]}', OpenAIDecodeStatus.UNSUPPORTED),
    ),
)
def test_openai_raw_decoder_fails_closed(raw: bytes, status: OpenAIDecodeStatus) -> None:
    assert decode_openai_response(raw).status is status
