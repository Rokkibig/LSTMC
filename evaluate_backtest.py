"""
Backtest evaluation script with financial metrics
Calculates Sharpe Ratio, Sortino Ratio, Max Drawdown, Win Rate, etc.
"""

import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime


def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Розраховує Sharpe Ratio
    Annualized Sharpe Ratio assuming 252 trading days
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


def calculate_sortino_ratio(returns, risk_free_rate=0.0):
    """
    Розраховує Sortino Ratio (враховує тільки downside volatility)
    """
    if len(returns) == 0:
        return 0.0
    excess_returns = returns - risk_free_rate
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    return np.sqrt(252) * excess_returns.mean() / downside_returns.std()


def calculate_max_drawdown(equity_curve):
    """
    Розраховує максимальну просадку (Max Drawdown)
    """
    if len(equity_curve) == 0:
        return 0.0
    cumulative = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - cumulative) / cumulative
    return abs(drawdown.min())


def calculate_calmar_ratio(returns, max_drawdown):
    """
    Розраховує Calmar Ratio (annualized return / max drawdown)
    """
    if max_drawdown == 0:
        return 0.0
    annualized_return = returns.mean() * 252
    return annualized_return / max_drawdown


def calculate_win_rate(trades):
    """
    Розраховує відсоток виграшних трейдів
    """
    if len(trades) == 0:
        return 0.0
    winning_trades = sum(1 for t in trades if t > 0)
    return winning_trades / len(trades)


def calculate_profit_factor(trades):
    """
    Розраховує Profit Factor (gross profit / gross loss)
    """
    if len(trades) == 0:
        return 0.0
    gross_profit = sum(t for t in trades if t > 0)
    gross_loss = abs(sum(t for t in trades if t < 0))
    if gross_loss == 0:
        return float('inf') if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def calculate_expectancy(trades):
    """
    Розраховує математичне очікування на трейд
    """
    if len(trades) == 0:
        return 0.0
    return np.mean(trades)


def calculate_risk_reward_ratio(trades):
    """
    Розраховує середнє співвідношення ризик/прибуток
    """
    if len(trades) == 0:
        return 0.0
    winning_trades = [t for t in trades if t > 0]
    losing_trades = [t for t in trades if t < 0]

    if len(winning_trades) == 0 or len(losing_trades) == 0:
        return 0.0

    avg_win = np.mean(winning_trades)
    avg_loss = abs(np.mean(losing_trades))

    if avg_loss == 0:
        return 0.0

    return avg_win / avg_loss


def load_signals_history(history_dir):
    """
    Завантажує історичні сигнали
    """
    import os
    signals = []
    for date_folder in sorted(os.listdir(history_dir)):
        signal_path = os.path.join(history_dir, date_folder, "signals.json")
        if os.path.exists(signal_path):
            with open(signal_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                signals.append({
                    'date': date_folder,
                    'signals': data.get('signals', [])
                })
    return signals


def simulate_trades(signals_history, initial_balance=10000, risk_per_trade=0.02):
    """
    Симулює трейди на основі історичних сигналів
    """
    balance = initial_balance
    equity_curve = [balance]
    trades = []
    trade_log = []

    for day_data in signals_history:
        date = day_data['date']
        daily_signals = day_data['signals']

        # Filter ACTIVE signals
        active_signals = [s for s in daily_signals if s['signal']['decision']['status'] == 'ACTIVE']

        for signal in active_signals:
            # Simplified trade simulation
            # В реальності треба враховувати TP/SL та реальні ціни
            confidence = signal['signal']['decision']['confidence']
            side = signal['signal']['primary']['side']

            # Simple random outcome based on confidence (для демонстрації)
            # В реальному бектесті треба використовувати історичні ціни
            outcome = np.random.choice([1, -1], p=[confidence, 1-confidence])

            risk_amount = balance * risk_per_trade
            if side == "LONG":
                profit = risk_amount * 1.5 if outcome > 0 else -risk_amount
            else:
                profit = risk_amount * 1.5 if outcome < 0 else -risk_amount

            balance += profit
            equity_curve.append(balance)
            trades.append(profit)
            trade_log.append({
                'date': date,
                'symbol': signal['symbol'],
                'side': side,
                'confidence': confidence,
                'profit': profit,
                'balance': balance
            })

    return np.array(equity_curve), trades, trade_log


def main():
    parser = argparse.ArgumentParser(description="Evaluate backtest with financial metrics")
    parser.add_argument("--history-dir", default="outputs/history", help="Directory with historical signals")
    parser.add_argument("--initial-balance", type=float, default=10000, help="Initial account balance")
    parser.add_argument("--risk-per-trade", type=float, default=0.02, help="Risk per trade as % of balance")
    parser.add_argument("--output", default="outputs/backtest_report.json", help="Output report file")
    args = parser.parse_args()

    print("[INFO] Loading signals history...")
    signals_history = load_signals_history(args.history_dir)
    print(f"[INFO] Loaded {len(signals_history)} days of signals")

    print("[INFO] Running backtest simulation...")
    equity_curve, trades, trade_log = simulate_trades(
        signals_history,
        initial_balance=args.initial_balance,
        risk_per_trade=args.risk_per_trade
    )

    if len(trades) == 0:
        print("[WARN] No trades executed. Cannot calculate metrics.")
        return

    # Calculate returns
    returns = pd.Series(trades) / args.initial_balance

    # Calculate metrics
    final_balance = equity_curve[-1]
    total_return = (final_balance - args.initial_balance) / args.initial_balance
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    max_dd = calculate_max_drawdown(equity_curve)
    calmar = calculate_calmar_ratio(returns, max_dd)
    win_rate = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)
    expectancy = calculate_expectancy(trades)
    risk_reward = calculate_risk_reward_ratio(trades)

    # Create report
    report = {
        "generated_at": datetime.now().isoformat(),
        "initial_balance": args.initial_balance,
        "final_balance": float(final_balance),
        "total_return_pct": float(total_return * 100),
        "total_trades": len(trades),
        "winning_trades": int(sum(1 for t in trades if t > 0)),
        "losing_trades": int(sum(1 for t in trades if t < 0)),
        "metrics": {
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "max_drawdown_pct": float(max_dd * 100),
            "calmar_ratio": float(calmar),
            "win_rate_pct": float(win_rate * 100),
            "profit_factor": float(profit_factor),
            "expectancy": float(expectancy),
            "avg_risk_reward_ratio": float(risk_reward),
        },
        "trade_log": trade_log[-100:]  # Last 100 trades
    }

    # Print summary
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    print(f"Initial Balance:    ${args.initial_balance:,.2f}")
    print(f"Final Balance:      ${final_balance:,.2f}")
    print(f"Total Return:       {total_return*100:+.2f}%")
    print(f"Total Trades:       {len(trades)}")
    print(f"Win Rate:           {win_rate*100:.2f}%")
    print("\nPERFORMANCE METRICS")
    print("-"*60)
    print(f"Sharpe Ratio:       {sharpe:.3f}")
    print(f"Sortino Ratio:      {sortino:.3f}")
    print(f"Max Drawdown:       {max_dd*100:.2f}%")
    print(f"Calmar Ratio:       {calmar:.3f}")
    print(f"Profit Factor:      {profit_factor:.3f}")
    print(f"Expectancy:         ${expectancy:.2f}")
    print(f"Risk/Reward Ratio:  {risk_reward:.3f}")
    print("="*60)

    # Save report
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Report saved to {args.output}")


if __name__ == "__main__":
    main()
