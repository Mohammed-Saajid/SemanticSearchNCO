from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rank: int = Field(..., ge=1)
    id: str
    role_number: str
    role_title: str
    chunk_index: int
    chunk_text: str
    score: float
    combined_score: float

    occupational_title: str = Field(..., alias="Occupational Title")
    nco_2015: str = Field(..., alias="NCO 2015")
    nco_2004: str = Field(..., alias="NCO 2004")
    division: str = Field(..., alias="Division")
    sub_division: str = Field(..., alias="Sub Division")
    group: str = Field(..., alias="Group")
    family: str = Field(..., alias="Family")

    bm25_score: float | None = None
    vector_score: float | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem]


class RoleQueryRequest(BaseModel):
    role_number: str = Field(..., min_length=1, max_length=50)


class RoleDescriptionResponse(BaseModel):
    description: str
    role_number: str | None = None
    title: str | None = None


class RoleDetailResponse(BaseModel):
    role_number: str
    title: str
    old_regulation: str
    division: str = ""
    sub_division: str = ""
    group: str = ""
    family: str = ""
    description: str


class HealthResponse(BaseModel):
    status: str
    version: str
    vector_count: int
    role_count: int
    qdrant_status: bool
