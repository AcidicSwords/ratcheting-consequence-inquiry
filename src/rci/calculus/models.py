"""Strict data for the bounded succession--arrangement calculus.

These records represent syntax, candidates, and checked observations.  They contain no
callables and grant no execution, admission, checking, warrant, or promotion authority.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from rci.core.model import ArtifactRef, FrozenModel, Identifier
from rci.warrant.models import CheckReference


def _unique(values: tuple[str, ...], label: str, *, nonempty: bool = False) -> None:
    if nonempty and not values:
        raise ValueError(f"{label} must be nonempty")
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique")


class PortDirection(StrEnum):
    INPUT = "input"
    OUTPUT = "output"


class SortRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier


class PortSpec(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    sort_id: Identifier
    direction: PortDirection


class InterfaceRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    port_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_ports(self) -> InterfaceRef:
        _unique(self.port_ids, "interface ports")
        return self


class AnswerCell(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    label: Identifier
    value_artifact: ArtifactRef | None = None


class ReturnInterface(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    answer_cells: tuple[AnswerCell, ...]
    applicability_exterior_cell_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_cells(self) -> ReturnInterface:
        ids = tuple(cell.id for cell in self.answer_cells)
        _unique(ids, "return-interface answer cells", nonempty=True)
        if self.applicability_exterior_cell_id in set(ids):
            raise ValueError("applicability exterior is not a semantic sibling answer")
        return self


class EffectSignature(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    input_interface_id: Identifier
    return_interface_id: Identifier
    operation_id: Identifier


class EffectRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    signature_id: Identifier
    represented_only: Literal[True] = True


class RealizedInteractionPair(FrozenModel):
    """One binding-derived effect/return pair; not a ledger event or arrangement term."""

    schema_version: Literal[1] = 1
    id: Identifier
    represented_effect_id: Identifier
    external_return_id: Identifier
    return_interface_id: Identifier
    answer_cell_id: Identifier


class RealizedSuccession(FrozenModel):
    """A binding-declared linear ordering of realized pairs."""

    schema_version: Literal[1] = 1
    id: Identifier
    binding_revision: Identifier
    realized_pair_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_pairs(self) -> RealizedSuccession:
        _unique(self.realized_pair_ids, "realized succession pairs")
        return self


class ArrangementRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    input_interface_id: Identifier
    output_interface_id: Identifier


class PrimitiveArrangement(ArrangementRef):
    kind: Literal["primitive"] = "primitive"
    binding_primitive_id: Identifier


class IdentityArrangement(ArrangementRef):
    kind: Literal["identity"] = "identity"

    @model_validator(mode="after")
    def validate_identity(self) -> IdentityArrangement:
        if self.input_interface_id != self.output_interface_id:
            raise ValueError("identity arrangement requires one exact interface")
        return self


class SequentialArrangement(ArrangementRef):
    kind: Literal["sequential"] = "sequential"
    first_arrangement_id: Identifier
    second_arrangement_id: Identifier
    hidden_interface_id: Identifier


class ParallelArrangement(ArrangementRef):
    kind: Literal["parallel"] = "parallel"
    left_arrangement_id: Identifier
    right_arrangement_id: Identifier


class HideArrangement(ArrangementRef):
    kind: Literal["hide"] = "hide"
    source_arrangement_id: Identifier
    hidden_port_ids: tuple[Identifier, ...]
    reopening_key_id: Identifier

    @model_validator(mode="after")
    def validate_hidden_ports(self) -> HideArrangement:
        _unique(self.hidden_port_ids, "hidden ports", nonempty=True)
        return self


class CaseArrangement(ArrangementRef):
    kind: Literal["case"] = "case"
    distinction_id: Identifier
    branch_arrangement_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_branches(self) -> CaseArrangement:
        _unique(self.branch_arrangement_ids, "case branches", nonempty=True)
        return self


class CrossArrangement(ArrangementRef):
    kind: Literal["cross"] = "cross"
    source_arrangement_id: Identifier
    permutation: tuple[int, ...]

    @model_validator(mode="after")
    def validate_permutation(self) -> CrossArrangement:
        if tuple(sorted(self.permutation)) != tuple(range(len(self.permutation))):
            raise ValueError("crossing must be a finite total permutation")
        return self


class TransportArrangement(ArrangementRef):
    kind: Literal["transport"] = "transport"
    source_arrangement_id: Identifier
    bridge_id: Identifier
    preservation_check: CheckReference


class ReentryArrangement(ArrangementRef):
    kind: Literal["reentry"] = "reentry"
    target_arrangement_id: Identifier
    guard_effect_id: Identifier


Arrangement = Annotated[
    PrimitiveArrangement
    | IdentityArrangement
    | SequentialArrangement
    | ParallelArrangement
    | HideArrangement
    | CaseArrangement
    | CrossArrangement
    | TransportArrangement
    | ReentryArrangement,
    Field(discriminator="kind"),
]


class RelationSignature(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    port_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_ports(self) -> RelationSignature:
        _unique(self.port_ids, "relation ports", nonempty=True)
        return self


class Variable(FrozenModel):
    kind: Literal["variable"] = "variable"
    id: Identifier
    sort_id: Identifier


class Constant(FrozenModel):
    kind: Literal["constant"] = "constant"
    id: Identifier
    sort_id: Identifier
    value_artifact: ArtifactRef


Term = Annotated[Variable | Constant, Field(discriminator="kind")]


class Truth(FrozenModel):
    kind: Literal["truth"] = "truth"


class Equality(FrozenModel):
    kind: Literal["equality"] = "equality"
    left: Term
    right: Term

    @model_validator(mode="after")
    def validate_sorts(self) -> Equality:
        if self.left.sort_id != self.right.sort_id:
            raise ValueError("equality requires identical term sorts")
        return self


class Holds(FrozenModel):
    kind: Literal["holds"] = "holds"
    relation_id: Identifier
    argument_ids: tuple[Identifier, ...]


class Complement(FrozenModel):
    kind: Literal["complement"] = "complement"
    formula_id: Identifier
    field_id: Identifier


class Conjunction(FrozenModel):
    kind: Literal["conjunction"] = "conjunction"
    formula_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_formulae(self) -> Conjunction:
        _unique(self.formula_ids, "conjuncts", nonempty=True)
        return self


class ExistentialHide(FrozenModel):
    kind: Literal["existential_hide"] = "existential_hide"
    formula_id: Identifier
    variable_ids: tuple[Identifier, ...]
    reopening_key_id: Identifier

    @model_validator(mode="after")
    def validate_variables(self) -> ExistentialHide:
        _unique(self.variable_ids, "hidden variables", nonempty=True)
        return self


Formula = Annotated[
    Truth | Equality | Holds | Complement | Conjunction | ExistentialHide,
    Field(discriminator="kind"),
]


class OpenRelation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    relation_signature_id: Identifier
    formula_id: Identifier
    bound_port_ids: tuple[Identifier, ...]
    open_port_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_partition(self) -> OpenRelation:
        _unique(self.bound_port_ids, "bound ports")
        _unique(self.open_port_ids, "open ports")
        if set(self.bound_port_ids).intersection(self.open_port_ids):
            raise ValueError("bound and open relation ports must be disjoint")
        return self


class RelationExtension(FrozenModel):
    """One finite extensional interpretation used by the dependency-free checker."""

    schema_version: Literal[1] = 1
    id: Identifier
    relation_signature_id: Identifier
    port_ids: tuple[Identifier, ...]
    rows: tuple[tuple[Identifier, ...], ...]

    @model_validator(mode="after")
    def validate_rows(self) -> RelationExtension:
        _unique(self.port_ids, "relation-extension ports", nonempty=True)
        if any(len(row) != len(self.port_ids) for row in self.rows):
            raise ValueError("relation rows must match exact port arity")
        if tuple(sorted(set(self.rows))) != self.rows:
            raise ValueError("relation rows must be unique and canonically ordered")
        return self


class RelationComposition(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    left_relation_id: Identifier
    right_relation_id: Identifier
    hidden_port_id: Identifier
    reopening_key_id: Identifier
    extension: RelationExtension


class CompletionProfile(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    question_frame_id: Identifier
    completion_ids: tuple[Identifier, ...]
    cell_by_completion: tuple[tuple[Identifier, Identifier], ...]
    closed_registry_check: CheckReference | None = None

    @model_validator(mode="after")
    def validate_profile(self) -> CompletionProfile:
        _unique(self.completion_ids, "completion-profile identities", nonempty=True)
        mapped = tuple(item[0] for item in self.cell_by_completion)
        _unique(mapped, "mapped completion identities", nonempty=True)
        if set(mapped) != set(self.completion_ids):
            raise ValueError("completion profile must classify every completion exactly")
        return self


class QuestionPartition(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    profile_id: Identifier
    completion_ids_by_cell: tuple[tuple[Identifier, tuple[Identifier, ...]], ...]

    @model_validator(mode="after")
    def validate_partition(self) -> QuestionPartition:
        cell_ids = tuple(item[0] for item in self.completion_ids_by_cell)
        _unique(cell_ids, "question-partition cells", nonempty=True)
        for _, completion_ids in self.completion_ids_by_cell:
            _unique(completion_ids, "question-partition completions", nonempty=True)
            if tuple(sorted(completion_ids)) != completion_ids:
                raise ValueError("partition completions must be canonically ordered")
        return self


class InterrogativeOperatorRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    version: Identifier


class Question(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    operator: InterrogativeOperatorRef
    return_interface_id: Identifier
    applicability_policy_id: Identifier
    comparison_policy_id: Identifier
    renderer_id: Identifier
    standing: Literal["inert_candidate", "compatibility_precompiled"] = "inert_candidate"


class RelationalQuestionLowering(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    question_id: Identifier
    open_relation_id: Identifier
    preservation_check: CheckReference


class QuestionFrame(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    question_id: Identifier
    return_interface_id: Identifier
    answer_cells: tuple[AnswerCell, ...]
    applicability_exterior_cell_id: Identifier | None = None
    exterior_continuation_node_id: Identifier | None = None
    per_cell_continuation_node_ids: tuple[tuple[Identifier, Identifier], ...]
    discharge_mechanism_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_frame(self) -> QuestionFrame:
        cell_ids = tuple(cell.id for cell in self.answer_cells)
        _unique(cell_ids, "frame answer cells", nonempty=True)
        continuation_cells = tuple(item[0] for item in self.per_cell_continuation_node_ids)
        if set(continuation_cells) != set(cell_ids):
            raise ValueError("every semantic answer cell requires one continuation")
        _unique(continuation_cells, "frame continuation cells")
        _unique(self.discharge_mechanism_ids, "frame discharge mechanisms", nonempty=True)
        if self.applicability_exterior_cell_id in set(cell_ids):
            raise ValueError("applicability exterior is outside semantic siblings")
        if (self.applicability_exterior_cell_id is None) != (
            self.exterior_continuation_node_id is None
        ):
            raise ValueError("applicability exterior requires its distinct continuation")
        return self


class FrameObservationKind(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    EXTERIOR = "exterior"
    INDETERMINATE = "indeterminate"


class FrameObservation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    frame_id: Identifier
    kind: FrameObservationKind
    live_answer_cell_ids: tuple[Identifier, ...] = ()
    decode_outcome_id: Identifier | None = None
    check: CheckReference | None = None

    @model_validator(mode="after")
    def validate_observation(self) -> FrameObservation:
        _unique(self.live_answer_cell_ids, "live answer cells")
        if self.kind is FrameObservationKind.COMPLETE and len(self.live_answer_cell_ids) != 1:
            raise ValueError("complete observations select exactly one semantic cell")
        if self.kind is FrameObservationKind.PARTIAL and len(self.live_answer_cell_ids) < 2:
            raise ValueError("partial observations leave at least two cells live")
        if (
            self.kind in {FrameObservationKind.EXTERIOR, FrameObservationKind.INDETERMINATE}
            and self.live_answer_cell_ids
        ):
            raise ValueError("exterior and indeterminate outcomes are not semantic siblings")
        if self.kind is FrameObservationKind.INDETERMINATE and self.check is not None:
            raise ValueError("indeterminate decode is not a checked semantic observation")
        if self.kind is not FrameObservationKind.INDETERMINATE and self.check is None:
            raise ValueError("semantic/exterior observations require an independent check")
        return self


class EffectNode(FrozenModel):
    kind: Literal["effect"] = "effect"
    id: Identifier
    effect_id: Identifier
    return_interface_id: Identifier
    frame_id: Identifier


class ReturnNode(FrozenModel):
    kind: Literal["return"] = "return"
    id: Identifier
    value_artifact: ArtifactRef


class StopNode(FrozenModel):
    kind: Literal["stop"] = "stop"
    id: Identifier
    outcome: Literal["stop", "unknown"]


ProgramNode = Annotated[EffectNode | ReturnNode | StopNode, Field(discriminator="kind")]


class ContinuationEdge(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    source_node_id: Identifier
    answer_cell_id: Identifier
    target_node_id: Identifier


class InteractionProgram(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    entry_node_id: Identifier
    nodes: tuple[ProgramNode, ...]
    continuation_edges: tuple[ContinuationEdge, ...]
    effect_signatures: tuple[EffectSignature, ...]
    effects: tuple[EffectRef, ...]
    return_interfaces: tuple[ReturnInterface, ...]
    question_frames: tuple[QuestionFrame, ...]
    status: Literal["inert_candidate"] = "inert_candidate"


class ProgramActionKind(StrEnum):
    OPEN_OBLIGATION = "open_obligation"
    REQUEST_EXISTING_EFFECT = "request_existing_effect"
    REQUIRE_CHECK = "require_check"
    STOP = "stop"
    UNKNOWN = "unknown"


class ProgramAction(FrozenModel):
    kind: ProgramActionKind
    program_id: Identifier
    node_id: Identifier
    target_id: Identifier | None = None


class TraceFragmentRef(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    source_inquiry_id: Identifier
    realized_pair_ids: tuple[Identifier, ...]

    @model_validator(mode="after")
    def validate_pairs(self) -> TraceFragmentRef:
        _unique(self.realized_pair_ids, "fragment realized pairs", nonempty=True)
        return self


class ArrangementCandidate(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    arrangement: Arrangement
    fragment_ids: tuple[Identifier, ...]
    status: Literal["inert_candidate"] = "inert_candidate"

    @model_validator(mode="after")
    def validate_fragments(self) -> ArrangementCandidate:
        _unique(self.fragment_ids, "candidate fragments", nonempty=True)
        return self


class RecognitionWitness(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    candidate_id: Identifier
    reproduced_fragment_ids: tuple[Identifier, ...]
    discriminator_ids: tuple[Identifier, ...]
    check: CheckReference

    @model_validator(mode="after")
    def validate_witness(self) -> RecognitionWitness:
        _unique(self.reproduced_fragment_ids, "reproduced fragments", nonempty=True)
        _unique(self.discriminator_ids, "recognition discriminators", nonempty=True)
        return self


class PersistenceWitness(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    predecessor_arrangement_id: Identifier
    successor_arrangement_id: Identifier
    succession_fragment_id: Identifier
    protected_horizon_id: Identifier
    commutes: bool
    check: CheckReference
    residue_id: Identifier | None = None

    @model_validator(mode="after")
    def validate_residue(self) -> PersistenceWitness:
        if self.commutes == (self.residue_id is not None):
            raise ValueError(
                "failed persistence requires residue; commuting persistence forbids it"
            )
        return self


class ArrangementProgramAdmission(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    program_id: Identifier
    outcome: Literal["admit", "reject"]
    policy_version: Literal["g3k-program-policy-v1"] = "g3k-program-policy-v1"
    check: CheckReference


class InteractionOccurrence(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    program_id: Identifier
    node_id: Identifier
    effect_id: Identifier
    effect_request_id: Identifier
    source_sequence: int = Field(ge=1)


class InteractionFrameObservation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    occurrence_id: Identifier
    observation: FrameObservation


class InteractionContinuation(FrozenModel):
    schema_version: Literal[1] = 1
    id: Identifier
    occurrence_id: Identifier
    observation_id: Identifier
    selected_answer_cell_id: Identifier
    successor_node_id: Identifier
