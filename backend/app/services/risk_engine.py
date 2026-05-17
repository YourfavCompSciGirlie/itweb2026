def calculate_risk_score(data: dict) -> dict:
    """
    Combines all fraud signals into a single risk score (0-100).
    Inputs:
        - sim_swap_minutes_ago: how recent was the SIM swap
        - amount: transaction amount in Rands
        - gnn_fraud_score: score from Matshepo's GNN (0-100)
        - channel: USSD | MOBILE_APP | BRANCH
    """
    score = 0
    reasons = []

    # --- Signal 1: SIM Swap Recency ---
    sim_minutes = data.get("sim_swap_minutes_ago")
    if sim_minutes is not None:
        if sim_minutes < 60:          # Less than 1 hour
            score += 45
            reasons.append(f"SIM swapped {sim_minutes} mins ago (CRITICAL)")
        elif sim_minutes < 360:       # Less than 6 hours
            score += 30
            reasons.append(f"SIM swapped {sim_minutes} mins ago (HIGH)")
        elif sim_minutes < 1440:      # Less than 24 hours
            score += 15
            reasons.append(f"SIM swapped {sim_minutes} mins ago (MEDIUM)")

    # --- Signal 2: Transaction Amount ---
    amount = data.get("amount", 0)
    if amount > 20000:
        score += 25
        reasons.append(f"Very large amount: R{amount:,.2f}")
    elif amount > 10000:
        score += 15
        reasons.append(f"Large amount: R{amount:,.2f}")
    elif amount > 5000:
        score += 8
        reasons.append(f"Elevated amount: R{amount:,.2f}")

    # --- Signal 3: GNN Fraud Score (Matshepo's input) ---
    gnn_score = data.get("gnn_fraud_score")
    if gnn_score is not None:
        if gnn_score >= 80:
            score += 25
            reasons.append(f"GNN flagged recipient network (score: {gnn_score:.0f})")
        elif gnn_score >= 50:
            score += 15
            reasons.append(f"GNN suspicious recipient network (score: {gnn_score:.0f})")
        elif gnn_score >= 30:
            score += 5
            reasons.append(f"GNN mild concern on recipient (score: {gnn_score:.0f})")

    # --- Signal 4: Channel Risk ---
    channel = data.get("channel", "USSD")
    if channel == "USSD":
        score += 5
        reasons.append("USSD channel (lower security)")

    # --- Cap score at 100 ---
    score = min(score, 100)

    # --- Decision Logic ---
    if score >= 70:
        decision = "BLOCK"
    elif score >= 40:
        decision = "STEP_UP"
    else:
        decision = "ALLOW"

    return {
        "risk_score": score,
        "decision": decision,
        "reason": " | ".join(reasons) if reasons else "No risk factors detected"
    }