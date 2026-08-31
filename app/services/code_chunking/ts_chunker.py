from tree_sitter_language_pack import get_parser

from app.services.code_chunking.languages import get_language_config


def chunk_with_treesitter(content: str, extension: str) -> list[dict] | None:
    """
    Returns None if the extension has no config, or if parsing fails —
    caller falls back to naive chunking.

    Two structural things this handles that a naive top-level scan doesn't:
    1. Some grammars split a function/method's signature
       and body into SIBLING nodes rather than one node containing both
       body_pairing merges these back into one chunk per function/method.
    2. Classes are recursed into: each class produces a small "header"
       chunk (class declaration + fields, no method bodies) PLUS one
       separate chunk per method, tagged with parent_class in metadata.
    """
    config = get_language_config(extension)
    if config is None:
        return None

    try:
        parser = get_parser(config["ts_language"])
        tree = parser.parse(bytes(content, "utf-8"))
    except Exception:
        return None

    chunks: list[dict] = []
    leftover_ranges: list[tuple[int, int]] = []

    groups = _pair_signature_with_body(
        list(tree.root_node.children), config.get("body_pairing", {})
    )

    for group in groups:
        head, tail = group[0], group[-1]

        if head.type in config["container_types"]:
            class_chunk, method_chunks = _extract_class(head, tail, content, config)
            if class_chunk:
                chunks.append(class_chunk)
            chunks.extend(method_chunks)

        elif head.type in config["top_level_types"]:
            chunks.append(_make_chunk(head, tail, content, config, extra_metadata={}))

        else:
            leftover_ranges.append((head.start_byte, tail.end_byte))

    if leftover_ranges:
        leftover_text = "\n".join(content[s:e] for s, e in leftover_ranges).strip()
        if leftover_text:
            chunks.insert(
                0,
                {
                    "content": leftover_text,
                    "start_line": 1,
                    "end_line": None,
                    "chunk_metadata": {
                        "symbol": None,
                        "node_type": "module_level",
                        "language": config["ts_language"],
                    },
                },
            )

    return chunks


def _pair_signature_with_body(nodes: list, body_pairing: dict) -> list[list]:
    """
    Merges a node with its immediately-following sibling when the node's
    type is a body_pairing key and the next sibling's type matches the
    configured body type. Nodes not needing pairing pass through as
    single-element groups.
    """
    groups = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        expected_body_type = body_pairing.get(node.type)
        if (
            expected_body_type
            and i + 1 < len(nodes)
            and nodes[i + 1].type == expected_body_type
        ):
            groups.append([node, nodes[i + 1]])
            i += 2
        else:
            groups.append([node])
            i += 1
    return groups


def _make_chunk(head, tail, content: str, config: dict, extra_metadata: dict) -> dict:
    symbol = _extract_symbol_name(head, content)
    return {
        "content": content[head.start_byte : tail.end_byte],
        "start_line": head.start_point[0] + 1,
        "end_line": tail.end_point[0] + 1,
        "chunk_metadata": {
            "symbol": symbol,
            "node_type": head.type,
            "language": config["ts_language"],
            **extra_metadata,
        },
    }


def _extract_class(
    head, tail, content: str, config: dict
) -> tuple[dict | None, list[dict]]:
    """
    Splits a class into a header chunk (declaration + fields, no method
    bodies) and one chunk per method. Falls back to treating the whole
    class as one chunk if the configured body-wrapper node isn't found —
    this is the graceful-degradation path if container_body_wrapper is
    ever wrong for a language (e.g. an unverified Python/JS guess).
    """
    class_name = _extract_symbol_name(head, content)
    body_wrapper_type = config.get("container_body_wrapper")

    body_node = next((c for c in head.children if c.type == body_wrapper_type), None)
    if body_node is None:
        return _make_chunk(head, tail, content, config, extra_metadata={}), []

    body_groups = _pair_signature_with_body(
        list(body_node.children), config.get("body_pairing", {})
    )

    method_chunks = []
    field_ranges = []

    for group in body_groups:
        g_head, g_tail = group[0], group[-1]
        if g_head.type in config["method_types"]:
            method_chunks.append(
                _make_chunk(
                    g_head,
                    g_tail,
                    content,
                    config,
                    extra_metadata={"parent_class": class_name},
                )
            )
        else:
            field_ranges.append((g_head.start_byte, g_tail.end_byte))

    header_text = content[head.start_byte : body_node.start_byte].strip()
    field_text = "\n".join(content[s:e] for s, e in field_ranges).strip()
    header_content = (
        f"{header_text}\n{field_text}".strip() if field_text else header_text
    )

    class_chunk = {
        "content": header_content,
        "start_line": head.start_point[0] + 1,
        "end_line": body_node.start_point[0] + 1,
        "chunk_metadata": {
            "symbol": class_name,
            "node_type": head.type,
            "language": config["ts_language"],
            "method_count": len(method_chunks),
        },
    }
    return class_chunk, method_chunks


def _extract_symbol_name(node, content: str) -> str | None:
    """
    Looks for a direct identifier-like child. Falls back to recursing into
    any child node whose type name contains "signature" (Dart alone has
    at least: function_signature, constructor_signature,
    factory_constructor_signature — discovered by trial, not documented
    anywhere convenient, so matching on the naming convention generalizes
    to unseen variants like const/operator signatures rather than requiring
    another manual fix each time one surfaces).
    """
    name = _find_name_before_param_list(node, content)
    if name:
        return name

    for child in node.children:
        if child.type in ("identifier", "name", "type_identifier"):
            return content[child.start_byte : child.end_byte]

    for child in node.children:
        if "signature" in child.type:
            name = _find_name_before_param_list(child, content)
            if name:
                return name
            for grandchild in child.children:
                if grandchild.type in ("identifier", "name", "type_identifier"):
                    return content[grandchild.start_byte : grandchild.end_byte]

    return None


def _find_name_before_param_list(node, content: str) -> str | None:
    """
    Scans direct children for a parameter-list node, then returns the
    identifier-like child immediately before it. Handles both plain names
    and named-constructor patterns like 'ClassName.fromJson(...)' where
    the relevant identifier is still the one right before the parens.
    """
    children = list(node.children)
    param_list_types = ("formal_parameter_list", "parameters")
    for i, child in enumerate(children):
        if child.type in param_list_types and i > 0:
            prev = children[i - 1]
            if prev.type in ("identifier", "name"):
                return content[prev.start_byte : prev.end_byte]
    return None
