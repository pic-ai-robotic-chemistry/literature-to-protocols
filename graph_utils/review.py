from langchain_community.graphs.graph_document import GraphDocument

def graph_doc_to_payload(doc: GraphDocument):
    return {
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "properties": getattr(n, "properties", {}) or {}
            }
            for n in doc.nodes
        ],
        "relationships": [
            {
                "rid": i,
                "source": r.source.id if hasattr(r.source, "id") else r.source,
                "target": r.target.id if hasattr(r.target, "id") else r.target,
                "type": r.type,
                "properties": getattr(r, "properties", {}) or {}
            }
            for i, r in enumerate(doc.relationships)
        ]
    }

import json
from langchain.chat_models import ChatOpenAI
from langchain_community.graphs.graph_document import GraphDocument

def review_graph_document(llm: ChatOpenAI, doc: GraphDocument):
    payload = graph_doc_to_payload(doc)

    prompt = f"""
You are doing a very conservative review of an extracted knowledge graph against a scientific text.

Goal:
- Preserve almost everything.
- Most items should remain unchanged.
- Only report very obvious, text-grounded fixes.
- When uncertain, keep unchanged.

Rules:
- Do not regenerate the graph.
- Do not add missing knowledge.
- Do not rewrite broadly.
- Keep scientific details, experimental details, conditions, methods, steps, and reported results.
- Do not remove or simplify items just because they are detailed, numeric, sample-specific, procedural, or could be represented differently.
- Only FIX if there is a clear and obvious text-grounded error.
- Fixes must be minimal.

Source text:
{doc.source.page_content}

Extracted graph:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Return valid JSON only, no markdown, no extra text.

Return JSON with this exact structure:
{{
  "fixed_nodes": [
    {{
      "original_id": "...",
      "corrected": {{
        "id": "...",
        "type": "...",
        "properties": {{}}
      }},
      "reason": "..."
    }}
  ],
  "fixed_relationships": [
    {{
      "rid": 0,
      "corrected": {{
        "source": "...",
        "target": "...",
        "type": "...",
        "properties": {{}}
      }},
      "reason": "..."
    }}
  ]
}}

Important:
- Do not include unchanged items.
- If nothing clearly needs to change, return empty lists.
"""
    resp = llm.invoke(prompt)
    return json.loads(resp.content if hasattr(resp, "content") else resp)

from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument

def apply_review(doc: GraphDocument, review: dict):
    fixed_nodes = {
        item["original_id"]: item["corrected"]
        for item in review.get("fixed_nodes", [])
    }

    fixed_relationships = {
        item["rid"]: item["corrected"]
        for item in review.get("fixed_relationships", [])
    }

    # nodes：默认全部保留，只应用 fix
    new_nodes = []
    node_map = {}

    for n in doc.nodes:
        if n.id in fixed_nodes:
            c = fixed_nodes[n.id]
            new_node = Node(
                id=c["id"],
                type=c["type"],
                properties=c.get("properties", {}) or {}
            )
        else:
            new_node = n

        new_nodes.append(new_node)
        node_map[n.id] = new_node

    # 如果 node id 被改了，补上映射
    for original_id, corrected in fixed_nodes.items():
        node_map[corrected["id"]] = node_map[original_id]

    # relationships：默认全部保留，只应用 fix
    new_relationships = []

    for rid, r in enumerate(doc.relationships):
        if rid in fixed_relationships:
            c = fixed_relationships[rid]
            s_id = c["source"]
            t_id = c["target"]
            rel_type = c["type"]
            props = c.get("properties", {}) or {}
        else:
            s_id = r.source.id if hasattr(r.source, "id") else r.source
            t_id = r.target.id if hasattr(r.target, "id") else r.target
            rel_type = r.type
            props = getattr(r, "properties", {}) or {}

        if s_id not in node_map or t_id not in node_map:
            continue

        new_relationships.append(
            Relationship(
                source=node_map[s_id],
                target=node_map[t_id],
                type=rel_type,
                properties=props
            )
        )

    return GraphDocument(
        nodes=new_nodes,
        relationships=new_relationships,
        source=doc.source
    )