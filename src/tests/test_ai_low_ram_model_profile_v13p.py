from ai_kernel.profiles import default_model_profiles


def test_qwen06b_profile_is_registered():
    profiles = {p.profile_id: p for p in default_model_profiles()}
    assert "qwen3-local-0.6b" in profiles
    assert profiles["qwen3-local-0.6b"].model == "qwen3:0.6b"
    assert profiles["qwen3-local-0.6b"].admin_enabled is True


def test_qwen06b_is_local_first_and_vietnamese():
    profiles = {p.profile_id: p for p in default_model_profiles()}
    p = profiles["qwen3-local-0.6b"]
    assert p.local_first is True
    assert "vietnamese" in {cap.value for cap in p.capabilities}
