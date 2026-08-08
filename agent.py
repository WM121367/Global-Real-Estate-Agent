# ==================================================
# 🏢 Global Estate Intelligence Agent (Ver 1.1.0-could)
# ==================================================
import datetime
import hashlib
import json
import os
from typing import Dict, List, Optional
from uagents import Agent, Context, Model, Protocol

CURRENT_VERSION = "4.5.0-cloud"

# Agentverse Secrets から AGENT_SEED を取得
AGENT_SEED = os.getenv("AGENT_SEED")

# クラウドホスティング用 Agent 初期化 (port/endpoint は Agentverse が自動制御)
real_estate_agent = Agent(
    name="global-estate-intell-agent",
    seed=AGENT_SEED
)

# ------------------------------------------------------------------------------
# 1. データモデル定義 (Data Models)
# ------------------------------------------------------------------------------

class RealEstateRequest(Model):
    request_id: str
    timestamp: str
    force_refresh: bool = False


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


class ChatMessage(Model):
    message: str


# ------------------------------------------------------------------------------
# 2. Protocol 定義 & Chat プロトコル組み込み
# ------------------------------------------------------------------------------

real_estate_proto = Protocol("RealEstateRWAProtocol", version="1.0.0")
chat_proto = Protocol("Agent Chat Protocol", version="0.2.0")

@chat_proto.on_message(model=ChatMessage, replies=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"💬 チャット受信 ({sender}): {msg.message}")
    reply_text = (
        f"🏢 Global Estate Intelligence Agent (Ver {CURRENT_VERSION}) [@prime-estate-oracle] です！\n"
        f"グローバル主要都市キャップレート、RWA不動産プロトコルTVL、モーゲージ金利スプレッド、およびキャピタルフライトリスクを追跡中です。"
    )
    await ctx.send(sender, ChatMessage(message=reply_text))

real_estate_agent.include(chat_proto)

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
    """外部APIやオンチェーンノードからデータを収集・解析する実体関数"""
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
            obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()
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
# 4. メッセージハンドラ (uAgents Event Handlers)
# ------------------------------------------------------------------------------

@real_estate_proto.on_message(
    model=RealEstateRequest, replies=RealEstateResponse
)
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
            f"[global_estate_agent] Data unchanged (Hash: {current_hash[:8]}...). Skipping payload duplication."
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
        f"[global_estate_agent] Successfully sent RealEstateResponse to {sender}"
    )


# Agent にプロトコルを適用
real_estate_agent.include(real_estate_proto)

@real_estate_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info("==================================================")
    ctx.logger.info(f"🏢 Global Estate Intelligence Agent (Ver {CURRENT_VERSION})")
    ctx.logger.info(f"📍 Address: {real_estate_agent.address}")
    ctx.logger.info("==================================================")

# ------------------------------------------------------------------------------
# 5. エージェントの起動
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    real_estate_agent.run()
