from factory.agents.factory_agent import FactoryAgent


def test_factory_can_design_and_scaffold() -> None:
    result = FactoryAgent().design_and_scaffold("Create a simple research assistant")
    assert result.spec.name
    assert result.files
    assert any(file.path.endswith("agent.py") for file in result.files)
