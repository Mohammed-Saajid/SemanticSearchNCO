from typing import List, Optional
from pydantic import AliasChoices, BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=100)
    bm25_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    vector_weight: float = Field(default=0.6, ge=0.0, le=1.0)


class SearchResultItem(BaseModel):
    id: str
    role_number: str
    role_title: str
    chunk_index: int
    chunk_text: str
    score: float
    combined_score: float

    occupational_title: str
    nco_2015: str
    nco_2004: str
    division: str
    sub_division: str
    group: str
    family: str

    occupational_title_alias: str = Field(
        alias="Occupational Title",
        validation_alias=AliasChoices("occupational_title_alias", "Occupational Title", "occupational_title"),
    )
    nco_2015_alias: str = Field(
        alias="NCO 2015",
        validation_alias=AliasChoices("nco_2015_alias", "NCO 2015", "nco_2015"),
    )
    nco_2004_alias: str = Field(
        alias="NCO 2004",
        validation_alias=AliasChoices("nco_2004_alias", "NCO 2004", "nco_2004"),
    )
    division_alias: str = Field(
        alias="Division",
        validation_alias=AliasChoices("division_alias", "Division", "division"),
    )
    sub_division_alias: str = Field(
        alias="Sub Division",
        validation_alias=AliasChoices("sub_division_alias", "Sub Division", "sub_division"),
    )
    group_alias: str = Field(
        alias="Group",
        validation_alias=AliasChoices("group_alias", "Group", "group"),
    )
    family_alias: str = Field(
        alias="Family",
        validation_alias=AliasChoices("family_alias", "Family", "family"),
    )

    bm25_score: Optional[float] = None
    vector_score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]


class RoleQueryRequest(BaseModel):
    role_number: str = Field(..., min_length=1, max_length=50)


class RoleDescriptionResponse(BaseModel):
    description: str
    role_number: Optional[str] = None
    title: Optional[str] = None


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
