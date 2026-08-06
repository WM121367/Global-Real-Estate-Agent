# real_estate_agent.py
"""World Money Map (Ver 4.1.0) - Real Estate & RWA Analysis Agent

uAgents Framework を使用し、オーケストレーターおよび他 Agent と相互通信を行う
第5の子エージェント実装。
"""

import datetime
import hashlib
import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from uagents import Agent, Context, Model, Protocol
from pydantic import BaseModel, Field
from uagents import Agent, Context, Model, Protocol
# ------------------------------------------------------------------------------
# 1. データモデル定義 (Data Models)
# ------------------------------------------------------------------------------

class RealEstateRequest(Model):
    request_id: str
    timestamp: str
    force_refresh: bool = False  # Default値はイコールで指定


class RWATokenMetrics(Model):
    protocol: str
    tvl_usd: float
    volume_24h_usd: float
    market_cap_usd: float
    avg_yield_apy: float


class CapRateAndIndex(Model):
    city: str
    country: str
    residential_cap_rate: float
    commercial_cap_rate: float
    house_price_index_yoy: float


class MacroInterestAnalysis(Model):
    us10y_yield: float
    mortgage_30y_avg: float
    spread: float
    correlation_score: float
    market_sentiment: str


class CapitalFlightAndRisk(Model):
    target_region: str
    capital_inflow_est_usd_m: float
    regulatory_risk_score: int
    liquidity_risk_score: int
    estimated_roi: float


class RealEstateResponse(Model):
    request_id: str
    timestamp: str
    rwa_token_metrics: list[RWATokenMetrics]
    global_cap_rates: list[CapRateAndIndex]
    macro_interest: MacroInterestAnalysis
    capital_flight_risk: list[CapitalFlightAndRisk]
    data_hash: str

# ------------------------------------------------------------------------------
# 2. Agent 初期設定 & Protocol 定義
# ------------------------------------------------------------------------------

# Secretタブ（環境変数）から安全に読み込む
SEED_PHRASE = os.getenv("AGENT_SEED")

if not SEED_PHRASE:
    raise ValueError(
        "環境変数 AGENT_SEED が設定されていません。Secretタブを確認してください。"
    )

AGENT_PORT = 8005
AGENT_ENDPOINT = [f"http://127.0.0.1:{AGENT_PORT}/submit"]

real_estate_agent = Agent(
    name="real_estate_agent",
    seed=SEED_PHRASE,
    port=AGENT_PORT,
    endpoint=AGENT_ENDPOINT,
    publish_manifest=True,  # Almanac 登録およびサービス発見を有効化
)

real_estate_proto = Protocol("RealEstateRWAProtocol", version="1.0.0")

# ------------------------------------------------------------------------------
# 3. データ取得 & 分析ロジック (内部処理)
# ------------------------------------------------------------------------------


def fetch_real_estate_data() -> (
    tuple[
        List[RWATokenMetrics],
        List[CapRateAndIndex],
        MacroInterestAnalysis,
        List[CapitalFlightAndRisk],
    ]
):
    """外部APIやオンチェーンノードからデータを収集・解析する実体関数（サンプルデータ生成）"""
    rwa_tokens = [
        RWATokenMetrics(
            protocol="RealT",
            tvl_usd=105000000.0,
            volume_24h_usd=1200000.0,
            market_cap_usd=105000000.0,
            avg_yield_apy=9.8,
        ),
        RWATokenMetrics(
            protocol="Propy",
            tvl_usd=45000000.0,
            volume_24h_usd=3500000.0,
            market_cap_usd=82000000.0,
            avg_yield_apy=6.2,
        ),
        RWATokenMetrics(
            protocol="Centrifuge (Real Estate Pools)",
            tvl_usd=210000000.0,
            volume_24h_usd=850000.0,
            market_cap_usd=210000000.0,
            avg_yield_apy=8.5,
        ),
    ]

    cap_rates = [
        CapRateAndIndex(
            city="Tokyo",
            country="Japan",
            residential_cap_rate=3.4,
            commercial_cap_rate=4.1,
            house_price_index_yoy=4.2,
        ),
        CapRateAndIndex(
            city="New York",
            country="USA",
            residential_cap_rate=5.2,
            commercial_cap_rate=6.5,
            house_price_index_yoy=-1.1,
        ),
        CapRateAndIndex(
            city="London",
            country="UK",
            residential_cap_rate=4.8,
            commercial_cap_rate=5.9,
            house_price_index_yoy=0.5,
        ),
        CapRateAndIndex(
            city="Dubai",
            country="UAE",
            residential_cap_rate=7.1,
            commercial_cap_rate=8.3,
            house_price_index_yoy=12.4,
        ),
    ]

    macro = MacroInterestAnalysis(
        us10y_yield=4.25,
        mortgage_30y_avg=6.85,
        spread=2.60,
        correlation_score=-0.82,
        market_sentiment="Bearish",
    )

    capital_flight = [
        CapitalFlightAndRisk(
            target_region="Dubai",
            capital_inflow_est_usd_m=1450.0,
            regulatory_risk_score=4,
            liquidity_risk_score=3,
            estimated_roi=11.2,
        ),
        CapitalFlightAndRisk(
            target_region="Tokyo",
            capital_inflow_est_usd_m=890.0,
            regulatory_risk_score=2,
            liquidity_risk_score=2,
            estimated_roi=5.8,
        ),
        CapitalFlightAndRisk(
            target_region="Singapore",
            capital_inflow_est_usd_m=620.0,
            regulatory_risk_score=3,
            liquidity_risk_score=3,
            estimated_roi=6.5,
        ),
    ]

    return rwa_tokens, cap_rates, macro, capital_flight


def compute_payload_hash(rwa, cap, macro, flight) -> str:
    """データの同一性を判定するためのSHA256ハッシュを計算"""

    def to_dict(obj):
        return (
            obj.model_dump()
            if hasattr(obj, "model_dump")
            else obj.dict()
        )

    raw_str = json.dumps(
        {
            "rwa": [to_dict(item) for item in rwa],
            "cap": [to_dict(item) for item in cap],
            "macro": to_dict(macro),
            "flight": [to_dict(item) for item in flight],
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

# ------------------------------------------------------------------------------
# 4. メッセージハンドラ & 重複チェックロジック (uAgents Event Handlers)
# ------------------------------------------------------------------------------

@real_estate_proto.on_message(model=RealEstateRequest, replies=RealEstateResponse)
async def handle_real_estate_request(
    ctx: Context, sender: str, msg: RealEstateRequest
):
    # 1. データの収集・解析
    rwa_tokens, cap_rates, macro, capital_flight = fetch_real_estate_data()
    current_hash = compute_payload_hash(
        rwa_tokens, cap_rates, macro, capital_flight
    )

    # 2. ctx.storage を使用した重複データ送信防止チェック
    last_sent_hash = ctx.storage.get("last_sent_hash")

    if not msg.force_refresh and last_sent_hash == current_hash:
        ctx.logger.info(
            f"[{ctx.name}] Data unchanged (Hash: {current_hash[:8]}...). Skipping payload duplication."
        )

    # ハッシュおよびタイムスタンプの更新
    ctx.storage.set("last_sent_hash", current_hash)
    ctx.storage.set("last_updated_at", datetime.datetime.utcnow().isoformat())

    # 3. レスポンス構築と返信
    response = RealEstateResponse(
        request_id=msg.request_id,
        timestamp=datetime.datetime.utcnow().isoformat(),
        rwa_token_metrics=rwa_tokens,
        global_cap_rates=cap_rates,
        macro_interest=macro,
        capital_flight_risk=capital_flight,
        data_hash=current_hash,
    )

    await ctx.send(sender, response)
    ctx.logger.info(
        f"[{ctx.name}] Successfully sent RealEstateResponse to {sender}"
    )

# Agent にプロトコルを適用
real_estate_agent.include(real_estate_proto)

# ------------------------------------------------------------------------------
# 5. エージェントの起動
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting Real Estate Agent on address: {real_estate_agent.address}")
    real_estate_agent.run()
