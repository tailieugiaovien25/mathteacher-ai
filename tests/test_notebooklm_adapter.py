from notebooklm_bridge.adapters.notebooklm import (
    NotebookLMAdapter,
    NotebookLMAdapterConfig,
)


def main():
    adapter = NotebookLMAdapter(
        NotebookLMAdapterConfig(enabled=False)
    )

    assert adapter.enabled is False

    try:
        adapter.sync_source(
            notebook_id="notebook-001",
            document_id="document-001",
        )
    except RuntimeError as error:
        assert str(error) == "NotebookLM integration is disabled"
    else:
        raise AssertionError(
            "Disabled NotebookLM adapter must reject synchronization"
        )

    print("NOTEBOOKLM_ADAPTER_GOVERNANCE_TEST_OK")


if __name__ == "__main__":
    main()