"""Тесты Artifact Store."""

from tester_agent.infrastructure.artifacts import ArtifactStore


def test_create_run_and_save(tmp_path):
    store = ArtifactStore(root=tmp_path / ".testagent")
    run_dir = store.create_run()
    assert run_dir.exists()

    store.save_prompt([{"role": "user", "content": "hi"}], "resp")
    store.save_generated("SomeClass.method", "def test():\n    pass\n")

    assert (run_dir / "prompts" / "001_messages.json").exists()
    assert (run_dir / "prompts" / "001_response.txt").exists()
    assert (run_dir / "generated" / "SomeClass_method.py").exists()
