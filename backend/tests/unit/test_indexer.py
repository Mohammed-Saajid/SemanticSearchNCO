from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.indexer import IndexingService


def test_parse_raw_data_list(indexing_service: IndexingService):
    data = [
        {
            "role_number": "2001.0100",
            "Role Name": "Civil Engineer",
            "2004 Regulation": "2001.1",
            "Role Description": "Plans and designs civil infrastructures and bridges.",
        }
    ]
    roles, chunks = indexing_service.parse_raw_data(data)
    assert len(roles) == 1
    assert roles[0].role_number == "2001.0100"
    assert roles[0].title == "Civil Engineer"
    assert len(chunks) >= 1


def test_parse_raw_data_dict(indexing_service: IndexingService):
    data = {
        "3001.0100": {
            "Role Name": "Mechanical Engineer",
            "Role Description": "Designs mechanical tools and industrial equipment.",
        }
    }
    roles, chunks = indexing_service.parse_raw_data(data)
    assert len(roles) == 1
    assert roles[0].role_number == "3001.0100"
    assert roles[0].title == "Mechanical Engineer"
    assert len(chunks) >= 1


def test_index_data_full_flow(
    indexing_service: IndexingService,
    role_repository: RoleRepository,
    vector_repository: VectorRepository,
):
    data = [
        {
            "role_number": "4001.0100",
            "Role Name": "Electrical Engineer",
            "Role Description": "Designs and tests electrical systems and circuits.",
        },
        {
            "role_number": "4001.0200",
            "Role Name": "Chemical Engineer",
            "Role Description": "Develops chemical processes for converting raw materials.",
        },
    ]

    stats = indexing_service.index_data(data)
    assert stats["indexed_roles"] == 2
    assert stats["indexed_chunks"] >= 2

    assert role_repository.count() == 2
    assert vector_repository.count() >= 2
