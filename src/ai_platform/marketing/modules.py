from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketingModule:
    module_id: str
    label: str
    mode: str
    description: str


MARKETING_MODULES = (
    MarketingModule("market_research", "Market Research", "draft", "Tổng hợp insight thị trường từ dữ liệu được phép sử dụng."),
    MarketingModule("content_marketing", "Content Marketing", "draft", "Tạo nội dung nháp theo kênh và đối tượng."),
    MarketingModule("product_marketing", "Product Marketing", "draft", "Soạn thông điệp tính năng, lợi ích và tài liệu giới thiệu."),
    MarketingModule("campaign_assistant", "Campaign Assistant", "human_approved", "Lập kế hoạch chiến dịch; phát hành cần người duyệt."),
    MarketingModule("customer_insight", "Customer Insight", "read_only", "Phân tích phản hồi khách hàng đã được cấp quyền."),
    MarketingModule("sales_assistant", "Sales Assistant", "human_approved", "Soạn kịch bản/bản nháp bán hàng; không tự cam kết."),
    MarketingModule("crm_assistant", "CRM Assistant", "human_approved", "Hỗ trợ phân tích CRM; không tự sửa hồ sơ khách hàng."),
    MarketingModule("analytics", "Marketing Analytics", "read_only", "Tổng hợp chỉ số và giải thích dữ liệu chiến dịch."),
)


def marketing_modules() -> tuple[MarketingModule, ...]:
    return MARKETING_MODULES
