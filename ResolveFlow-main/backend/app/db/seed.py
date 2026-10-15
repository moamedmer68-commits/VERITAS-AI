from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import KnowledgeDocument, Order, User
from app.services.rag import embed_text


KNOWLEDGE_SEEDS = [
    {
        "title": "七天无理由退货政策",
        "source": "policy/refund.md",
        "content": "商品签收后七个自然日内，保持商品、配件和包装完整，可申请无理由退货。已激活的软件、定制商品及影响二次销售的商品不适用。质量问题退货由平台承担运费。退款申请属于资金写操作，必须经过人工客服审批。",
    },
    {
        "title": "物流与配送说明",
        "source": "policy/shipping.md",
        "content": "普通订单付款后四十八小时内发货。已发货订单可通过订单号查询承运商和物流单号。物流超过七十二小时未更新时，应创建高优先级工单并转交物流专员。",
    },
    {
        "title": "电子产品保修规则",
        "source": "policy/warranty.md",
        "content": "耳机、键盘等电子产品提供十二个月有限保修。非人为质量问题可申请检修或换货。进液、摔损、非官方拆修不在保修范围内。提交售后时需要订单号、故障描述和必要的图片证据。",
    },
    {
        "title": "人工客服升级规则",
        "source": "operations/handoff.md",
        "content": "涉及人身安全、法律投诉、重复扣款、账户盗用或用户连续两次明确要求人工服务时，应立即创建高优先级工单并转接人工客服，不应继续自动承诺处理结果。",
    },
]


def seed_database(db: Session) -> None:
    customer = db.scalar(select(User).where(User.email == "customer@resolveflow.dev"))
    if customer is None:
        customer = User(
            email="customer@resolveflow.dev",
            full_name="演示用户",
            role="customer",
            password_hash=hash_password("customer123"),
        )
        db.add(customer)

    admin = db.scalar(select(User).where(User.email == "admin@resolveflow.dev"))
    if admin is None:
        admin = User(
            email="admin@resolveflow.dev",
            full_name="客服主管",
            role="admin",
            password_hash=hash_password("admin123"),
        )
        db.add(admin)
    db.flush()

    if db.scalar(select(Order).limit(1)) is None:
        db.add_all(
            [
                Order(
                    id="RF20260801001",
                    user_id=customer.id,
                    product_name="Aurora Pro 无线耳机",
                    amount=699.0,
                    status="shipped",
                    tracking_number="SF202608010889",
                    purchased_at=datetime.now(UTC) - timedelta(days=2),
                    refundable=True,
                ),
                Order(
                    id="RF20260718007",
                    user_id=customer.id,
                    product_name="FlowType 机械键盘",
                    amount=459.0,
                    status="delivered",
                    tracking_number="YT202607190271",
                    purchased_at=datetime.now(UTC) - timedelta(days=20),
                    refundable=False,
                ),
            ]
        )

    if db.scalar(select(KnowledgeDocument).limit(1)) is None:
        db.add_all(
            [
                KnowledgeDocument(
                    title=item["title"],
                    source=item["source"],
                    content=item["content"],
                    embedding=embed_text(item["content"]),
                    chunk_count=1,
                )
                for item in KNOWLEDGE_SEEDS
            ]
        )
    db.commit()
