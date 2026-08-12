import json
from collections import defaultdict
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "canonical"
    / "mathematics"
    / "grade_06"
    / "curriculum_nodes.json"
)


def load_data() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_curriculum_nodes_file_exists():
    assert DATA_FILE.exists()


def test_grade_and_curriculum_ref():
    data = load_data()

    assert data["schema_version"] == 1
    assert data["curriculum_ref"] == "CURRICULUM-MATH-2018"
    assert data["grade"] == 6


def test_all_43_nodes_exist_in_canonical_order():
    data = load_data()
    nodes = data["nodes"]

    expected_ids = [
        f"CURR-NODE-MATH-G6-{i:03d}"
        for i in range(1, 44)
    ]

    assert len(nodes) == 43
    assert [
        node["curriculum_node_id"]
        for node in nodes
    ] == expected_ids


def test_node_ids_and_codes_are_unique():
    data = load_data()
    nodes = data["nodes"]

    ids = [node["curriculum_node_id"] for node in nodes]
    codes = [node["code"] for node in nodes]

    assert len(ids) == len(set(ids))
    assert len(codes) == len(set(codes))


def test_all_nodes_are_active_and_well_formed():
    data = load_data()

    allowed_types = {
        "CONTENT_STRAND",
        "CONTENT_DOMAIN",
        "CONTENT_GROUP",
        "CONTENT_ITEM",
    }

    for node in data["nodes"]:
        assert node["status"] == "ACTIVE"
        assert node["node_type"] in allowed_types
        assert isinstance(node["sequence"], int)
        assert node["sequence"] >= 1
        assert node["name"].strip()
        assert node["code"].strip()


def test_every_parent_reference_exists():
    data = load_data()
    nodes = data["nodes"]

    ids = {
        node["curriculum_node_id"]
        for node in nodes
    }

    for node in nodes:
        parent_id = node["parent_id"]

        if parent_id is not None:
            assert parent_id in ids


def test_root_strands_are_correct():
    data = load_data()

    roots = [
        node
        for node in data["nodes"]
        if node["parent_id"] is None
    ]

    assert [
        node["curriculum_node_id"]
        for node in roots
    ] == [
        "CURR-NODE-MATH-G6-001",
        "CURR-NODE-MATH-G6-015",
        "CURR-NODE-MATH-G6-031",
    ]

    assert [
        node["name"]
        for node in roots
    ] == [
        "Số và Đại số",
        "Hình học và Đo lường",
        "Một số yếu tố Thống kê và Xác suất",
    ]

    assert [
        node["sequence"]
        for node in roots
    ] == [1, 2, 3]


def test_sibling_sequences_are_unique():
    data = load_data()

    children_by_parent = defaultdict(list)

    for node in data["nodes"]:
        children_by_parent[node["parent_id"]].append(node)

    for siblings in children_by_parent.values():
        sequences = [
            node["sequence"]
            for node in siblings
        ]

        assert len(sequences) == len(set(sequences))


def test_number_hierarchy_is_correct():
    data = load_data()

    nodes = {
        node["curriculum_node_id"]: node
        for node in data["nodes"]
    }

    assert nodes["CURR-NODE-MATH-G6-002"]["parent_id"] == "CURR-NODE-MATH-G6-001"

    for node_id in (
        "CURR-NODE-MATH-G6-003",
        "CURR-NODE-MATH-G6-007",
        "CURR-NODE-MATH-G6-010",
        "CURR-NODE-MATH-G6-013",
    ):
        assert nodes[node_id]["parent_id"] == "CURR-NODE-MATH-G6-002"

    assert nodes["CURR-NODE-MATH-G6-004"]["parent_id"] == "CURR-NODE-MATH-G6-003"
    assert nodes["CURR-NODE-MATH-G6-005"]["parent_id"] == "CURR-NODE-MATH-G6-003"
    assert nodes["CURR-NODE-MATH-G6-006"]["parent_id"] == "CURR-NODE-MATH-G6-003"

    assert nodes["CURR-NODE-MATH-G6-008"]["parent_id"] == "CURR-NODE-MATH-G6-007"
    assert nodes["CURR-NODE-MATH-G6-009"]["parent_id"] == "CURR-NODE-MATH-G6-007"

    assert nodes["CURR-NODE-MATH-G6-011"]["parent_id"] == "CURR-NODE-MATH-G6-010"
    assert nodes["CURR-NODE-MATH-G6-012"]["parent_id"] == "CURR-NODE-MATH-G6-010"

    assert nodes["CURR-NODE-MATH-G6-014"]["parent_id"] == "CURR-NODE-MATH-G6-013"


def test_geometry_hierarchy_is_correct():
    data = load_data()

    nodes = {
        node["curriculum_node_id"]: node
        for node in data["nodes"]
    }

    assert nodes["CURR-NODE-MATH-G6-016"]["parent_id"] == "CURR-NODE-MATH-G6-015"
    assert nodes["CURR-NODE-MATH-G6-024"]["parent_id"] == "CURR-NODE-MATH-G6-015"

    assert nodes["CURR-NODE-MATH-G6-017"]["parent_id"] == "CURR-NODE-MATH-G6-016"
    assert nodes["CURR-NODE-MATH-G6-020"]["parent_id"] == "CURR-NODE-MATH-G6-016"

    assert nodes["CURR-NODE-MATH-G6-018"]["parent_id"] == "CURR-NODE-MATH-G6-017"
    assert nodes["CURR-NODE-MATH-G6-019"]["parent_id"] == "CURR-NODE-MATH-G6-017"

    for node_id in (
        "CURR-NODE-MATH-G6-021",
        "CURR-NODE-MATH-G6-022",
        "CURR-NODE-MATH-G6-023",
    ):
        assert nodes[node_id]["parent_id"] == "CURR-NODE-MATH-G6-020"

    assert nodes["CURR-NODE-MATH-G6-025"]["parent_id"] == "CURR-NODE-MATH-G6-024"
    assert nodes["CURR-NODE-MATH-G6-029"]["parent_id"] == "CURR-NODE-MATH-G6-024"

    for node_id in (
        "CURR-NODE-MATH-G6-026",
        "CURR-NODE-MATH-G6-027",
        "CURR-NODE-MATH-G6-028",
    ):
        assert nodes[node_id]["parent_id"] == "CURR-NODE-MATH-G6-025"

    assert nodes["CURR-NODE-MATH-G6-030"]["parent_id"] == "CURR-NODE-MATH-G6-029"


def test_statistics_probability_hierarchy_is_correct():
    data = load_data()

    nodes = {
        node["curriculum_node_id"]: node
        for node in data["nodes"]
    }

    for node_id in (
        "CURR-NODE-MATH-G6-032",
        "CURR-NODE-MATH-G6-038",
        "CURR-NODE-MATH-G6-042",
    ):
        assert nodes[node_id]["parent_id"] == "CURR-NODE-MATH-G6-031"

    assert nodes["CURR-NODE-MATH-G6-033"]["parent_id"] == "CURR-NODE-MATH-G6-032"
    assert nodes["CURR-NODE-MATH-G6-036"]["parent_id"] == "CURR-NODE-MATH-G6-032"

    assert nodes["CURR-NODE-MATH-G6-034"]["parent_id"] == "CURR-NODE-MATH-G6-033"
    assert nodes["CURR-NODE-MATH-G6-035"]["parent_id"] == "CURR-NODE-MATH-G6-033"
    assert nodes["CURR-NODE-MATH-G6-037"]["parent_id"] == "CURR-NODE-MATH-G6-036"

    assert nodes["CURR-NODE-MATH-G6-039"]["parent_id"] == "CURR-NODE-MATH-G6-038"
    assert nodes["CURR-NODE-MATH-G6-040"]["parent_id"] == "CURR-NODE-MATH-G6-039"
    assert nodes["CURR-NODE-MATH-G6-041"]["parent_id"] == "CURR-NODE-MATH-G6-039"

    assert nodes["CURR-NODE-MATH-G6-043"]["parent_id"] == "CURR-NODE-MATH-G6-042"


def test_key_terminal_nodes_have_expected_names():
    data = load_data()

    nodes = {
        node["curriculum_node_id"]: node
        for node in data["nodes"]
    }

    assert nodes["CURR-NODE-MATH-G6-019"]["name"] == (
        "Hình chữ nhật, hình thoi, hình bình hành, hình thang cân"
    )

    assert nodes["CURR-NODE-MATH-G6-028"]["name"] == (
        "Góc. Các góc đặc biệt. Số đo góc"
    )

    assert nodes["CURR-NODE-MATH-G6-037"]["name"] == (
        "Hình thành và giải quyết vấn đề đơn giản xuất hiện "
        "từ các số liệu và biểu đồ thống kê đã có"
    )

    assert nodes["CURR-NODE-MATH-G6-043"]["name"] == (
        "Sử dụng phần mềm để vẽ biểu đồ"
    )
