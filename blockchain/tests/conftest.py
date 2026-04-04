from collections import defaultdict

from pytest import Config, Function, Session


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Function]) -> None:
    """Ensure unit tests run before integration tests.

    Rules (in order):
    - If a test is marked with @pytest.mark.integration, treat it as integration.
    - Otherwise, if the file path contains a path segment named "integration",
      treat it as integration.
    - All integration tests are moved after non-integration tests. Relative order
      is preserved within each group.
    """

    folder_order = ["tests/unit", "tests/integration", "tests/system"]

    sorted_items: dict[int, list[Function]] = defaultdict(list)
    enumerated_folder = list(enumerate(folder_order))

    for item in items:
        idx = next(idx for idx, x in enumerated_folder if x in str(item.fspath))
        sorted_items[idx].append(item)

    items.clear()
    for idx, _ in enumerated_folder:
        items.extend(sorted_items[idx])
