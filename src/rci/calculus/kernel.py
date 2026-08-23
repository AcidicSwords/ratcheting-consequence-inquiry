"""Pure validation and interpretation for the bounded G3K kernel."""

from __future__ import annotations

from collections import defaultdict

from rci.calculus.models import (
    Arrangement,
    CompletionProfile,
    ContinuationEdge,
    CrossArrangement,
    EffectNode,
    FrameObservation,
    FrameObservationKind,
    InteractionProgram,
    ProgramAction,
    ProgramActionKind,
    QuestionPartition,
    RelationComposition,
    RelationExtension,
    ReturnNode,
    SequentialArrangement,
    StopNode,
)


class CalculusValidationError(ValueError):
    """A represented term is ill-typed or structurally invalid."""


def compose_relation_extensions(
    left: RelationExtension,
    right: RelationExtension,
    *,
    hidden_port_id: str,
    composition_id: str,
    reopening_key_id: str,
) -> RelationComposition:
    """Join on one exact port and hide it, retaining reopening provenance."""

    if left.port_ids.count(hidden_port_id) != 1 or right.port_ids.count(hidden_port_id) != 1:
        raise CalculusValidationError("relation composition requires one shared hidden port")
    left_index = left.port_ids.index(hidden_port_id)
    right_index = right.port_ids.index(hidden_port_id)
    output_ports = tuple(item for item in left.port_ids if item != hidden_port_id) + tuple(
        item for item in right.port_ids if item != hidden_port_id
    )
    if len(output_ports) != len(set(output_ports)):
        raise CalculusValidationError("relation composition output interfaces overlap")
    rows = {
        tuple(value for index, value in enumerate(left_row) if index != left_index)
        + tuple(value for index, value in enumerate(right_row) if index != right_index)
        for left_row in left.rows
        for right_row in right.rows
        if left_row[left_index] == right_row[right_index]
    }
    extension = RelationExtension(
        id=f"{composition_id}-extension",
        relation_signature_id=f"{composition_id}-signature",
        port_ids=output_ports,
        rows=tuple(sorted(rows)),
    )
    return RelationComposition(
        id=composition_id,
        left_relation_id=left.id,
        right_relation_id=right.id,
        hidden_port_id=hidden_port_id,
        reopening_key_id=reopening_key_id,
        extension=extension,
    )


def build_question_partition(profile: CompletionProfile) -> QuestionPartition:
    """Build a deterministic profile-relative partition without claiming completeness."""

    grouped: dict[str, list[str]] = defaultdict(list)
    for completion_id, cell_id in profile.cell_by_completion:
        grouped[cell_id].append(completion_id)
    return QuestionPartition(
        id=f"partition-{profile.id}",
        profile_id=profile.id,
        completion_ids_by_cell=tuple(
            (cell_id, tuple(sorted(completion_ids)))
            for cell_id, completion_ids in sorted(grouped.items())
        ),
    )


def question_is_productive(partition: QuestionPartition) -> bool:
    """A single cell is skipped; it never establishes absolute equivalence."""

    return len(partition.completion_ids_by_cell) > 1


def validate_arrangement_composition(
    composition: SequentialArrangement,
    *,
    arrangements: tuple[Arrangement, ...],
) -> None:
    """Validate beta after alpha; this is arrangement composition, never succession."""

    by_id = {item.id: item for item in arrangements}
    if len(by_id) != len(arrangements):
        raise CalculusValidationError("arrangement identities must be unique")
    first = by_id.get(composition.first_arrangement_id)
    second = by_id.get(composition.second_arrangement_id)
    if first is None or second is None:
        raise CalculusValidationError("composition operands must be owned")
    if first.output_interface_id != composition.hidden_interface_id:
        raise CalculusValidationError("first arrangement does not produce the hidden interface")
    if second.input_interface_id != composition.hidden_interface_id:
        raise CalculusValidationError("second arrangement does not consume the hidden interface")
    if composition.input_interface_id != first.input_interface_id:
        raise CalculusValidationError("composition input interface does not match first operand")
    if composition.output_interface_id != second.output_interface_id:
        raise CalculusValidationError("composition output interface does not match second operand")


def crossing_is_involutive(crossing: CrossArrangement) -> bool:
    """Return exact finite involution status; binary swap is the legacy Boolean Not case."""

    return all(
        crossing.permutation[crossing.permutation[index]] == index for index in crossing.permutation
    )


def _cycle_has_effect(
    start: str,
    current: str,
    *,
    adjacency: dict[str, list[str]],
    effect_ids: set[str],
    path: tuple[str, ...],
) -> bool:
    for target in adjacency.get(current, []):
        if target == start:
            return any(node_id in effect_ids for node_id in (*path, current))
        if target in path:
            continue
        if not _cycle_has_effect(
            start,
            target,
            adjacency=adjacency,
            effect_ids=effect_ids,
            path=(*path, current),
        ):
            return False
    return True


def validate_program(program: InteractionProgram) -> None:
    nodes = {node.id: node for node in program.nodes}
    if len(nodes) != len(program.nodes) or program.entry_node_id not in nodes:
        raise CalculusValidationError("program nodes must be unique and include the entry")
    signatures = {item.id: item for item in program.effect_signatures}
    effects = {item.id: item for item in program.effects}
    interfaces = {item.id: item for item in program.return_interfaces}
    frames = {item.id: item for item in program.question_frames}
    if len(signatures) != len(program.effect_signatures):
        raise CalculusValidationError("effect signatures must be unique")
    if (
        len(effects) != len(program.effects)
        or len(interfaces) != len(program.return_interfaces)
        or len(frames) != len(program.question_frames)
    ):
        raise CalculusValidationError("effects, return interfaces, and frames must be unique")
    edges_by_source: dict[str, list[ContinuationEdge]] = defaultdict(list)
    edge_ids: set[str] = set()
    for edge in program.continuation_edges:
        if (
            edge.id in edge_ids
            or edge.source_node_id not in nodes
            or edge.target_node_id not in nodes
        ):
            raise CalculusValidationError("continuation edges must be unique and node-owned")
        edge_ids.add(edge.id)
        edges_by_source[edge.source_node_id].append(edge)
    for node in program.nodes:
        outgoing = edges_by_source.get(node.id, [])
        if isinstance(node, EffectNode):
            effect = effects.get(node.effect_id)
            if effect is None:
                raise CalculusValidationError("effect node references an unowned effect")
            signature = signatures.get(effect.signature_id)
            if signature is None or signature.return_interface_id != node.return_interface_id:
                raise CalculusValidationError(
                    "effect node return interface does not match its signature"
                )
            interface = interfaces.get(node.return_interface_id)
            if interface is None:
                raise CalculusValidationError("effect node return interface is not owned")
            frame = frames.get(node.frame_id)
            if frame is None or frame.return_interface_id != interface.id:
                raise CalculusValidationError("effect node requires its exact owned answer frame")
            if tuple(cell.id for cell in frame.answer_cells) != tuple(
                cell.id for cell in interface.answer_cells
            ):
                raise CalculusValidationError("effect frame and return-interface cells differ")
            if frame.applicability_exterior_cell_id != interface.applicability_exterior_cell_id:
                raise CalculusValidationError("effect frame applicability exterior differs")
            expected = {cell.id for cell in interface.answer_cells}
            if interface.applicability_exterior_cell_id is not None:
                expected.add(interface.applicability_exterior_cell_id)
            actual = {edge.answer_cell_id for edge in outgoing}
            if expected != actual or len(outgoing) != len(expected):
                raise CalculusValidationError(
                    "effect continuation must cover each answer cell exactly"
                )
            declared_targets = dict(frame.per_cell_continuation_node_ids)
            if (
                frame.applicability_exterior_cell_id is not None
                and frame.exterior_continuation_node_id is not None
            ):
                declared_targets[frame.applicability_exterior_cell_id] = (
                    frame.exterior_continuation_node_id
                )
            actual_targets = {edge.answer_cell_id: edge.target_node_id for edge in outgoing}
            if actual_targets != declared_targets:
                raise CalculusValidationError(
                    "effect continuation edges must equal the antecedent frame table"
                )
        elif outgoing:
            raise CalculusValidationError(
                "only effect nodes may select answer-conditioned continuations"
            )
    adjacency = {
        source: [edge.target_node_id for edge in edges] for source, edges in edges_by_source.items()
    }
    effect_ids = {node.id for node in program.nodes if isinstance(node, EffectNode)}
    for node_id in nodes:
        if not _cycle_has_effect(
            node_id,
            node_id,
            adjacency=adjacency,
            effect_ids=effect_ids,
            path=(),
        ):
            raise CalculusValidationError("program contains an epsilon cycle")


def interpret_node(program: InteractionProgram, node_id: str) -> ProgramAction:
    """Return inert work; interpretation cannot actualize the represented operation."""

    validate_program(program)
    node = next((item for item in program.nodes if item.id == node_id), None)
    if node is None:
        return ProgramAction(kind=ProgramActionKind.UNKNOWN, program_id=program.id, node_id=node_id)
    if isinstance(node, EffectNode):
        return ProgramAction(
            kind=ProgramActionKind.REQUEST_EXISTING_EFFECT,
            program_id=program.id,
            node_id=node.id,
            target_id=node.effect_id,
        )
    if isinstance(node, ReturnNode):
        return ProgramAction(
            kind=ProgramActionKind.REQUIRE_CHECK,
            program_id=program.id,
            node_id=node.id,
        )
    if isinstance(node, StopNode):
        return ProgramAction(
            kind=(ProgramActionKind.STOP if node.outcome == "stop" else ProgramActionKind.UNKNOWN),
            program_id=program.id,
            node_id=node.id,
        )
    return ProgramAction(kind=ProgramActionKind.UNKNOWN, program_id=program.id, node_id=node_id)


def select_continuation(
    program: InteractionProgram,
    *,
    node_id: str,
    observation: FrameObservation,
) -> str | None:
    """Select only a checked complete branch; partial/exterior/Unknown never guess."""

    validate_program(program)
    if observation.kind is not FrameObservationKind.COMPLETE:
        return None
    cell_id = observation.live_answer_cell_ids[0]
    matches = tuple(
        edge
        for edge in program.continuation_edges
        if edge.source_node_id == node_id and edge.answer_cell_id == cell_id
    )
    if len(matches) != 1:
        raise CalculusValidationError("checked answer does not determine one continuation")
    return matches[0].target_node_id
