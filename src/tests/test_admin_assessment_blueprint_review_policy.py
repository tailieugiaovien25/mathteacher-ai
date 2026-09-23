"""Visible actions must match the production blueprint approval trigger."""

from portal_v2.ui.admin_assessment_blueprint_review_streamlit import _review_action


def test_draft_owner_must_have_approved_locked_setting():
    assert _review_action(reviewer_user_id='owner', owner_user_id='owner',
                          status='DRAFT', setting_status='DRAFT', setting_locked=False) == 'SETTING_REQUIRED'
    assert _review_action(reviewer_user_id='owner', owner_user_id='owner',
                          status='DRAFT', setting_status='APPROVED', setting_locked=True) == 'SUBMIT'


def test_pending_blueprint_allows_admin_to_review_any_owner():
    assert _review_action(reviewer_user_id='owner', owner_user_id='owner',
                          status='PENDING_REVIEW', setting_status='APPROVED', setting_locked=True) == 'ADMIN_REVIEW'
    assert _review_action(reviewer_user_id='second-admin', owner_user_id='owner',
                          status='PENDING_REVIEW', setting_status='APPROVED', setting_locked=True) == 'ADMIN_REVIEW'
