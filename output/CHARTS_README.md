# Analysis Visualizations

All charts use complete labels: descriptive title, x-axis label with units, y-axis label with units, legend for multi-series charts, and readable value labels where practical.

## Consistent Palette
- primary (#1f77b4): baseline business metric emphasis
- secondary (#ff7f0e): comparative series
- success (#2ca02c): positive growth/composition
- warning (#d62728): anomalies and risk highlights
- neutral (#7f7f7f): reference lines and contextual guides

## Chart 1: Revenue by Product Line
- Type: Horizontal bar chart
- Question: Which product line generates the most revenue in the last quarter?
- Key Insight: Product A leads with $147K.
- Annotation: Arrow highlights the highest-revenue product for prioritization.

## Chart 2: Revenue Trend
- Type: Multi-series line chart
- Question: How has monthly revenue changed over 12 months for top products?
- Key Insight: The combined top-3 revenue trough occurs in Oct 2025.
- Annotation: Marker identifies the monthly revenue dip to trigger root-cause review.

## Chart 3: Order Value Distribution
- Type: Histogram
- Question: What order value ranges occur most frequently?
- Key Insight: Peak concentration is near $125 order values.
- Annotation: Callout marks the dominant bin that drives transaction volume.

## Chart 4: Revenue Composition
- Type: Stacked bar chart by quarter
- Question: How does product-line composition contribute to quarterly revenue?
- Key Insight: Product A contributes the largest share in the latest quarter.
- Annotation: Callout highlights the dominant product share in the latest quarter.

## Chart 5: Marketing vs Revenue
- Type: Scatter plot with trend line
- Question: Does higher marketing spend correlate with higher revenue?
- Key Insight: The relationship is strong with r=0.99.
- Annotation: Callout marks the weakest-performing spend-to-revenue outlier.
