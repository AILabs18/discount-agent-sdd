# Spec: Tiered Discount Logic

**Agent Role:** Pricing-Specialist-Agent

## 1. Business Rules

- **Standard Customers:** 0% discount.
- **Gold Customers:** 10% discount on orders over $100.
- **VIP Customers:** 20% discount on all orders.
- **Safety Cap:** No discount can ever exceed $500, regardless of tier.

## 2. Acceptance Criteria (The Tests)

- **GIVEN:** A 'Gold' customer with a $50 order.
- **THEN:** Discount should be $0 (Threshold not met).
- **GIVEN:** A 'VIP' customer with a $3,000 order.
- **THEN:** Discount should be $500 (Safety cap applied).
