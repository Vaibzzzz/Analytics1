

from enum import Enum

# ── Shared ChartType Enum ────────────────────────────────────
class ChartType(Enum):
    PIE   = "pie"
    BAR   = "bar"
    LIST  = "list"

# ── Drill‑level keys ─────────────────────────────────────────
DRILL_LVL1 = "DRILL_LVL1"
DRILL_LVL2 = "DRILL_LVL2"

# ── Per‑chart drill‐field options ────────────────────────────
# these are the only dimensions users can pick for each chart
chart_drill_options = {
    # for the Revenue by Currency pie
    "revenueByCurrency": [
        "issuer_country_code",
        "credit_card_type",
        "funding_source",
        "creation_type",
        "sca_type",
        "acquirer_name",       # join on acquirer_id → acquirer.name
        "fraud",
        "payment_successful",
        "country",
        "region",
    ],
    # for the Top 5 Acquirers bar
    "top5Acquirers": [
        "issuer_country_code",
        "credit_card_type",
        "funding_source",
        "creation_type",
        "sca_type",
        "currency",
        "fraud",
        "payment_successful",
        "country",
        "region",
    ],
    # for the Payment Method Distribution bar
    "paymentMethodDistribution": [
        "issuer_country_code",
        "currency",
        "funding_source",
        "creation_type",
        "sca_type",
        "acquirer_name",       # join on acquirer_id
        "fraud",
        "payment_successful",
        "country",
        "region",
    ],
    "processingFeeAnalysis": [
        "issuer_country_code",
        "credit_card_type",
        "funding_source",
        "creation_type",
        "sca_type",
        "currency",
        "fraud",
        "payment_successful",
        "country",
        "region",
    ],
    "salesByCurrency": [
        "issuer_country_code",
        "credit_card_type",
        "funding_source",
        "creation_type",
        "sca_type",
        "acquirer_name",       # join on acquirer_id → acquirer.name
        "fraud",
        "payment_successful",
        "country",
        "region",
    ],

}

# ── Drill‑level configs ───────────────────────────────────────
drill_configs = {
    DRILL_LVL1: {
        "title":       "{dimension_label} breakdown for {base_value}",
        "type":        ChartType.BAR,
        "drillable":   True,
        "drill_field": None,       # filled in at runtime
        "next_chart":  DRILL_LVL2,
    },
    DRILL_LVL2: {
        "title":       "{dimension_label} breakdown for {lvl1_value} ({lvl1_field_label}) for {base_value}",
        "type":        ChartType.BAR,
        "drillable":   False,
        "drill_field": None,
        "next_chart":  None,
    },
}

CHART_BASE_DIMENSION = {
    "revenueByCurrency":           "transaction_currency",
    "top5Acquirers":               "a.name",
    "paymentMethodDistribution":   "credit_card_type",    
    "salesByCurrency":             "transaction_currency",
    "processingFeeAnalysis":       "a.name"
 }

 # Map each top‐level chartKey to the aggregate expression
CHART_METRICS = {
    "revenueByCurrency":           "SUM(usd_value)::float",
    "top5Acquirers":               "COUNT(*)::float",
    "paymentMethodDistribution":   "COUNT(*)::float",
    "salesByCurrency":             "SUM(usd_value)::float",
    "processingFeeAnalysis":       "ROUND(SUM((t.pricing_ic/100.0)*t.usd_value + t.gateway_fee)/ NULLIF(SUM(t.usd_value),0) * 100, 2) "
}