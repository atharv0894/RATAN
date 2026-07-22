from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.entity.entity_extractor import EntityExtractor
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole, get_tenant_context
from app.exceptions import NotFoundError

router = APIRouter()
extractor = EntityExtractor()

class EntityResponse(BaseModel):
    id: str
    type: str
    value: str

class EntitySearchResponse(BaseModel):
    query: str
    results: List[EntityResponse]

class ExtractedEntitiesResponse(BaseModel):
    document_id: str
    entities: List[EntityResponse]

class EntityMention(BaseModel):
    document_id: str
    filename: str
    page_number: int
    section: str

class EntityDetailResponse(BaseModel):
    entity_value: str
    entity_type: str
    mentions: List[EntityMention]

@router.get("", response_model=APISuccessResponse[List[EntityResponse]])
def get_all_entities(current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer", "Operator"]))):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.* FROM entities e
        JOIN documents d ON e.document_id = d.id
        WHERE d.organization = ?
        GROUP BY e.entity_value
    """, (current_user["org_id"],))
    rows = cursor.fetchall()
    conn.close()
    
    response = []
    for r in rows:
        d = dict(r)
        response.append(EntityResponse(
            id=d.get("id", ""),
            type=d.get("entity_type"),
            value=d.get("entity_value")
        ))
    return APISuccessResponse(data=response)

@router.get("/{entity_name}", response_model=APISuccessResponse[EntitySearchResponse])
def search_entities_by_name(entity_name: str, current_user: dict = Depends(get_current_user)):
    results = extractor.search_entities(entity_name, current_user["org_id"])
    entities = []
    for r in results:
        entities.append(EntityResponse(
            id=r.get("id", ""),
            type=r.get("entity_type"),
            value=r.get("entity_value")
        ))
    return APISuccessResponse(data=EntitySearchResponse(query=entity_name, results=entities))

@router.get("/details/{entity_value}", response_model=APISuccessResponse[EntityDetailResponse])
def get_entity_details(entity_value: str, current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.entity_type, e.document_id, e.page_number, e.section, d.filename 
        FROM entities e
        JOIN documents d ON e.document_id = d.id
        WHERE e.entity_value = ? AND d.organization = ?
        ORDER BY e.created_at DESC
    """, (entity_value, current_user["org_id"]))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise NotFoundError("Entity", entity_value)
        
    mentions = []
    entity_type = rows[0]["entity_type"]
    
    # Deduplicate mentions by document and page
    seen = set()
    for row in rows:
        ident = (row["document_id"], row["page_number"])
        if ident not in seen:
            seen.add(ident)
            mentions.append(EntityMention(
                document_id=row["document_id"],
                filename=row["filename"],
                page_number=row["page_number"] or 1,
                section=row["section"] or "General"
            ))
            
    return APISuccessResponse(data=EntityDetailResponse(
        entity_value=entity_value,
        entity_type=entity_type,
        mentions=mentions
    ))

@router.get("/documents/{id}/entities", response_model=APISuccessResponse[ExtractedEntitiesResponse])
def get_document_entities(id: str, current_user: dict = Depends(get_current_user)):
    results = extractor.get_document_entities(id, current_user["org_id"])
    if not results:
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        doc = conn.cursor().execute("SELECT id FROM documents WHERE id = ? AND organization = ?", (id, current_user["org_id"])).fetchone()
        conn.close()
        if not doc:
            raise NotFoundError("Document", id)
            
    entities = []
    for r in results:
        entities.append(EntityResponse(
            id=r.get("id", ""),
            type=r.get("entity_type"),
            value=r.get("entity_value")
        ))
    return APISuccessResponse(data=ExtractedEntitiesResponse(document_id=id, entities=entities))

from typing import Optional, Dict, Any

class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    document_id: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    organization: Optional[str] = None
    metadata: Dict[str, Any] = {}
    group: int = 1
    val: float = 5.0

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    confidence: float
    metadata: Dict[str, Any] = {}

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    statistics: Dict[str, Any] = {}
    last_updated: float

@router.get("/graph/data", response_model=APISuccessResponse[GraphResponse])
def get_knowledge_graph(
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_tenant_context)
):
    from app.database.sqlite import get_db_connection
    import time
    conn = get_db_connection()
    cursor = conn.cursor()
    
    org_id = tenant["organization"]
    
    nodes_map = {}
    edges = []
    stats = {
        "Documents": 0, "Versions": 0, "Entities": 0, "Relationships": 0,
        "Organizations": 0, "Departments": 0, "Plants": 0, "Users": 0,
        "Pending Jobs": 0, "Completed Jobs": 0, "Failed Jobs": 0
    }
    
    # 1. Organization
    cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
    org = cursor.fetchone()
    if org:
        nodes_map[org_id] = GraphNode(id=org_id, type="Organization", label=org["name"], organization=org_id, group=8, val=20)
        stats["Organizations"] = 1
        
    # 2. Plants
    cursor.execute("SELECT * FROM plants WHERE org_id = ? AND is_deleted = 0", (org_id,))
    for p in cursor.fetchall():
        nodes_map[p["id"]] = GraphNode(id=p["id"], type="Plant", label=p["name"], organization=org_id, group=8, val=15)
        edges.append(GraphEdge(id=f"org_plant_{p['id']}", source=org_id, target=p["id"], relationship="contains", confidence=1.0))
        stats["Plants"] += 1
        
    # 3. Departments
    cursor.execute("SELECT d.* FROM departments d JOIN plants p ON d.plant_id = p.id WHERE p.org_id = ? AND d.is_deleted = 0", (org_id,))
    for d in cursor.fetchall():
        nodes_map[d["id"]] = GraphNode(id=d["id"], type="Department", label=d["name"], organization=org_id, group=8, val=12)
        edges.append(GraphEdge(id=f"plant_dept_{d['id']}", source=d["plant_id"], target=d["id"], relationship="contains", confidence=1.0))
        stats["Departments"] += 1

    # 4. Users
    cursor.execute("SELECT * FROM users WHERE org_id = ? AND is_deleted = 0", (org_id,))
    for u in cursor.fetchall():
        nodes_map[u["id"]] = GraphNode(id=u["id"], type="User", label=u["full_name"], organization=org_id, group=2, val=8)
        edges.append(GraphEdge(id=f"user_org_{u['id']}", source=u["id"], target=org_id, relationship="belongs_to", confidence=1.0))
        stats["Users"] += 1

    # 5. Documents
    cursor.execute("SELECT * FROM documents WHERE organization = ? AND deleted_at IS NULL", (org_id,))
    for doc in cursor.fetchall():
        nodes_map[doc["id"]] = GraphNode(id=doc["id"], type="Document", label=doc["filename"], status=doc["status"], organization=org_id, group=1, val=10)
        if doc["department"] and doc["department"] in nodes_map:
            edges.append(GraphEdge(id=f"doc_dept_{doc['id']}", source=doc["id"], target=doc["department"], relationship="belongs_to", confidence=1.0))
        if doc["owner"] and doc["owner"] in nodes_map:
            edges.append(GraphEdge(id=f"doc_owner_{doc['id']}", source=doc["id"], target=doc["owner"], relationship="uploaded_by", confidence=1.0))
        stats["Documents"] += 1

    # 6. Document Versions
    cursor.execute("SELECT v.* FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,))
    for v in cursor.fetchall():
        vid = v["id"]
        nodes_map[vid] = GraphNode(id=vid, type="Version", label=f"v{v['version_number']}", document_id=v["document_id"], version=str(v["version_number"]), status=v["status"], organization=org_id, group=1, val=6)
        edges.append(GraphEdge(id=f"ver_doc_{vid}", source=vid, target=v["document_id"], relationship="version_of", confidence=1.0))
        stats["Versions"] += 1

    # 7. Entities
    cursor.execute("SELECT e.* FROM entities e JOIN documents d ON e.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,))
    entities_added = set()
    for e in cursor.fetchall():
        ent_val = e["entity_value"]
        ent_type = e["entity_type"]
        if ent_val not in nodes_map:
            group_map = {"ROLE":2, "EQUIPMENT":3, "STANDARD":4, "SAFETY":5, "TOOL":6, "PARAMETER":7, "ORGANIZATION":8, "CONCEPT":9, "DOCUMENT":1}
            nodes_map[ent_val] = GraphNode(id=ent_val, type=ent_type, label=ent_val, organization=org_id, group=group_map.get(ent_type.upper(), 9), val=4)
            entities_added.add(ent_val)
        else:
            nodes_map[ent_val].val += 0.5 
            
        edge_id = f"doc_ent_{e['document_id']}_{ent_val}_{e['entity_id']}"
        edges.append(GraphEdge(id=edge_id, source=e["document_id"], target=ent_val, relationship="mentions", confidence=1.0))
    stats["Entities"] = len(entities_added)
    
    # 8. Jobs
    cursor.execute("""
        SELECT pj.status, COUNT(*) as c 
        FROM processing_jobs pj
        JOIN document_versions dv ON pj.target_id = dv.id
        JOIN documents d ON dv.document_id = d.id
        WHERE d.organization = ?
        GROUP BY pj.status
    """, (org_id,))
    for row in cursor.fetchall():
        if row["status"] == "COMPLETED": stats["Completed Jobs"] = row["c"]
        elif row["status"] == "FAILED": stats["Failed Jobs"] = row["c"]
        else: stats["Pending Jobs"] += row["c"]

    conn.close()
    
    stats["Relationships"] = len(edges)
    
    return APISuccessResponse(data=GraphResponse(
        nodes=list(nodes_map.values()),
        edges=edges,
        statistics=stats,
        last_updated=time.time()
    ))

