#!/usr/bin/env python3

# This script reproduces the reward and fee calculations usually done in Daml to verify that the
# values displayed in the SV wallet are correct.
# It was created based on the mainnet staging config on 2024-05-17. For other networks
# or after config changes on mainnet staging (in particular SV weight changes), some of the
# variables will need tweaking but the computation remains the same.

from decimal import Decimal, getcontext, ROUND_HALF_EVEN

# Set precision and rounding mode
getcontext().prec = 38
getcontext().rounding = ROUND_HALF_EVEN


# Daml Decimals have a precision of 38 and a scale of 10, i.e., 10 digits after the decimal point.
# Rounding is round_half_even.
class DamlDecimal:

    def __init__(self, decimal):
        if isinstance(decimal, str):
            self.decimal = Decimal(decimal).quantize(
                Decimal("0.0000000001"), rounding=ROUND_HALF_EVEN
            )
        else:
            self.decimal = decimal.quantize(
                Decimal("0.0000000001"), rounding=ROUND_HALF_EVEN
            )

    def __mul__(self, other):
        return DamlDecimal((self.decimal * other.decimal))

    def __add__(self, other):
        return DamlDecimal((self.decimal + other.decimal))

    def __radd__(self, other):
        return DamlDecimal((other + self.decimal))

    def __sub__(self, other):
        return DamlDecimal((self.decimal - other.decimal))

    def __truediv__(self, other):
        return DamlDecimal((self.decimal / other.decimal))

    def __str__(self):
        return self.decimal.__str__()

    def __eq__(self, other):
        return self.decimal == other.decimal


# Constants
minutes_per_hour = DamlDecimal("60")
hours_per_day = DamlDecimal("24")
days_per_year = DamlDecimal("365")
minutes_per_round = DamlDecimal("10")
# Calculate rounds per year
rounds_per_year = (minutes_per_hour * hours_per_day * days_per_year) / minutes_per_round
print(f"Rounds per year: {rounds_per_year}")
total_issuance_per_year = DamlDecimal("40000000000.0")
svs_percentage = DamlDecimal("0.80")
validators_percentage = DamlDecimal("0.05")
app_percentage = DamlDecimal("0.15")
amulet_price = DamlDecimal("0.005")
holding_fee_per_round_usd = DamlDecimal("1.0") / rounds_per_year
holding_fee_per_round = holding_fee_per_round_usd / amulet_price
validator_faucet_cap = DamlDecimal("2.85")
create_fee_usd = DamlDecimal("0.03")
create_fee = create_fee_usd / amulet_price


# Print holding fee per round
print(f"Holding fee per round (in usd): {holding_fee_per_round_usd}")
print(f"Holding fee per round (in cc): {holding_fee_per_round}")
print(f"Create fee (in usd): {create_fee_usd}")
print(f"Create fee (in cc): {create_fee}")

# Calculate issuance to SVs per round
issuance_per_round = total_issuance_per_year / rounds_per_year
issuance_to_svs_per_round = (
    issuance_per_round
    - validators_percentage * issuance_per_round
    - app_percentage * issuance_per_round
)
print(f"Issuance to SVs per round: {issuance_to_svs_per_round}")

# SV Reward Weights
sv_weights = {
    "Orb-1-LP-1": DamlDecimal("50000"),
    "Orb-1-LP-2": DamlDecimal("50000"),
    "Liberty-City-Ventures": DamlDecimal("100000"),
    "Global-Synchronizer-Foundation-Broadridge": DamlDecimal("100012"),
    "Global-Synchronizer-Foundation-GSF": DamlDecimal("100012"),
    "Global-Synchronizer-Foundation-7Ridge": DamlDecimal("100012"),
    "Global-Synchronizer-Foundation-TradeWeb": DamlDecimal("100012"),
    "Global-Synchronizer-Foundation-MPCH": DamlDecimal("9988"),
    "Global-Synchronizer-Foundation-DFNS": DamlDecimal("9988"),
    "Global-Synchronizer-Foundation-TheTie": DamlDecimal("9988"),
    "Global-Synchronizer-Foundation-Copper": DamlDecimal("9988"),
    "Digital-Asset-1": DamlDecimal("140000"),
    "Digital-Asset-2": DamlDecimal("140000"),
    "SV-Nodeops-Limited": DamlDecimal("100000"),
    "Cumberland-1": DamlDecimal("120000"),
    "Cumberland-2": DamlDecimal("120000"),
}

# Calculate total SV reward weight
total_sv_reward_weight = sum(sv_weights.values())
print(f"Total SV reward weight: {total_sv_reward_weight}")

# Calculate issuance per SV reward weight in basis points
issuance_per_sv_reward_weight_bps = issuance_to_svs_per_round / total_sv_reward_weight
print(f"Issuance per SV reward weight bps: {issuance_per_sv_reward_weight_bps}")

# Values from screenshots. This is currently left empty but fill in your own value in the form "beneficiaryname": DamlDecimal("value")
# to have the script check for equality.
# This is the SV rewards field in the "rewards created" section in transaction log in the wallet.
screenshot_issuances = {}

# Values from screenshots. This is currently left empty but fill in your own value in the form "beneficiaryname": DamlDecimal("value").
# This is the value at the very right in transaction log in the wallet.
screenshot_balance_changes = {}

# Note: This is the max issuance, the actual issuance goes down once there are either too many validator (non-faucet) rewards
# for the remainder of the validator percentage to be sufficient for this or there are too many validators requesting faucets coupons.
# Since the actual load can change round from round we skip over those computations here. On current mainnet staging everyone does get the max.
validator_faucet_issuance_per_coupon = validator_faucet_cap / amulet_price
print(
    f"Validator Faucet Reward (displayed as validator reward): {validator_faucet_issuance_per_coupon}"
)

# Calculate and display issuance for each SV based on their weight
for sv, weight in sv_weights.items():
    sv_issuance = issuance_per_sv_reward_weight_bps * weight
    screenshot_issuance = screenshot_issuances.get(sv)
    if screenshot_issuance:
        matches_issuance_screenshot_text = f"matches screenshot: {screenshot_issuance == sv_issuance} (screenshot: {screenshot_issuance})"
    else:
        matches_issuance_screenshot_text = "no screenshot"
    print(f"SV Reward for {sv}: {sv_issuance}, {matches_issuance_screenshot_text}")
    sv_balance_change = sv_issuance + validator_faucet_issuance_per_coupon - create_fee
    screenshot_balance_change = screenshot_balance_changes.get(sv)
    if screenshot_balance_change:
        matches_balance_change_screenshot_text = f"matches screenshot: {screenshot_balance_change == sv_balance_change} (screenshot: {screenshot_balance_change})"
    else:
        matches_balance_change_screenshot_text = "no screenshot"

    print(
        f"Balance change for {sv}: {sv_balance_change}, {matches_balance_change_screenshot_text}"
    )
