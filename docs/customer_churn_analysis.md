# Customer Churn Analysis: Executive Summary

## The Problem

Customer churn reduces recurring revenue and makes growth more expensive. The business needs to know which customer groups are most at risk, which are most valuable, and where support effort can protect revenue. This analysis turns customer, activity, support, and transaction records into a practical retention plan for product, operations, finance, and growth leaders.

## What We Examined

We examined 19 customer profile records across three segments: Enterprise, SMB, and Startup. The records include lifetime value, churn outcome, support-ticket count, retention days, and customer type. We also reviewed 30 transaction records for KPI context, 12 customer records for relationship patterns, and 90 daily revenue observations. These small sample fixtures show direction and priorities; the findings should be confirmed on the full customer base before budget commitments.

## What We Found

- **SMB is the clearest retention problem.** Its churn rate is 50.0%, the highest of the three segments, compared with 37.5% for Startup and 0.0% for Enterprise. The segment summary ranks SMB third for churn performance, where rank 1 is best.
  - **Supporting evidence:** The segment summary records SMB at 50.0% churn across six customers, and the heatmap makes the contrast visible. This identifies a specific group for immediate retention work.
- **Enterprise is the highest-value group and the strongest retention group.** Enterprise averages $159,000 in lifetime value and 463 retention days, while Startup averages $2,225 and 112 days.
  - **Supporting evidence:** The performer report ranks Enterprise first by lifetime value and retention, with five customers representing 26.3% of the sample. Protecting this high-value group can preserve more revenue than treating every customer identically.
- **Startup is the largest part of the base and has the shortest relationship.** Startup represents 42.1% of the sample and averages six support tickets and 112 retention days.
  - **Supporting evidence:** The segment summary shows the largest base share, highest average ticket volume, and lowest retention duration. Onboarding and self-service improvements could therefore reach the largest audience.
- **Support demand and churn move together.** Support tickets have a Pearson correlation of 0.879 with churn, while the rank-based comparison is 0.871.
  - **Supporting evidence:** The correlation report shows the relationship remains strong under both comparison methods. Support volume is a useful warning signal, but it does not prove that tickets cause churn; customer pain may drive both.
- **Revenue momentum weakened after a strong February.** February revenue was $4,775, up 29.4% from January; March was $4,735, down 0.8%, and the latest 30-day average fell 11.7%.
  - **Supporting evidence:** The time-series report identifies February as the highest month and the latest rolling trend as down. Retention action is more urgent when customer risk and revenue momentum are both unfavorable.

## Why This Is Happening

The pattern is consistent with customer friction concentrated outside Enterprise. SMB and Startup customers ask for more help, stay for less time, and are more likely to leave. The data cannot tell us whether support problems cause churn or whether a separate product problem causes both. The safe conclusion is that ticket volume is an early warning sign. Fast resolution and better onboarding should be tested to reduce customer pain.

## What We Recommend

1. **Launch an SMB retention sprint.** The Retention Manager and Customer Success Lead should review the six SMB records, group recurring issues, and contact at-risk customers. Start within 14 days and target a reduction from 50.0% to below 35% in the next 60-day cohort. Review weekly.
2. **Create Startup onboarding and self-service.** Product and Support should publish guided setup journeys, help content, and ticket-volume alerts. Deliver the first version within 30 days. Target 20% fewer average support tickets and retention above 112 days within 90 days.
3. **Protect Enterprise revenue while improving support.** Operations should maintain proactive Enterprise reviews and route high-value issues to an experienced queue while tracking support outcomes across segments. Implement within 30 days. Preserve Enterprise's 463-day retention and 0.0% sample churn without blocking support requests.

## Next Steps

Validate these priorities against the complete customer history, assign named owners, and review the three targets at the next monthly revenue meeting. The first decision should be whether the SMB and Startup patterns remain visible at production scale.