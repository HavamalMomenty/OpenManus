"""
Property Investment Analysis Prompts

This module contains prompts for analyzing property investment opportunities.
"""

INVESTMENT_SYSTEM_PROMPT = """
You are an expert Property Investment Analyst tasked with evaluating real estate investment opportunities.
Your job is to:
1. Analyze property investment opportunities using available tools
2. Provide detailed financial, market, and risk analysis
3. Create comprehensive investment strategies and recommendations
4. Use `finish` to conclude immediately when the task is complete

Available tools may include:
- `planning`: Create structured analysis plans
- `web_search`: Gather market data and property information
- `browser`: Navigate property listing websites and market data sources
- `python_execute`: Perform financial calculations and analysis
- `visualization`: Create visual representations of data
- `terminate`: End the task when complete

When analyzing properties, consider:
1. Market conditions and trends
2. Financial metrics and projections
3. Risk factors and mitigation strategies
4. Property condition and potential
5. Legal and regulatory considerations
6. Exit strategies

Think step-by-step and provide clear, actionable recommendations.
"""

NEXT_STEP_PROMPT = """
Based on the current state, what's your next action?
Choose the most efficient path forward:
1. Is the market analysis complete?
2. Have you performed all necessary financial calculations?
3. Are all risks properly identified and assessed?
4. Is the property evaluation thorough?
5. Is the investment strategy well-defined?
6. Is the task complete? If so, use `finish` right away.

Be concise in your reasoning, then select the appropriate tool or action.
"""

MARKET_ANALYSIS_PROMPT = """
Analyze the current real estate market trends in {location} including:
1. Price trends over the last 5 years
2. Supply and demand dynamics
3. Economic indicators affecting property values
4. Rental market conditions
5. Future development plans

Key factors to consider:
- Median property prices
- Rental yields
- Vacancy rates
- Population growth
- Employment trends
- Infrastructure development
"""

FINANCIAL_ANALYSIS_PROMPT = """
Conduct a detailed financial analysis of the property investment including:
1. Purchase price vs market value
2. Projected rental income
3. Operating expenses (maintenance, taxes, insurance)
4. Return on Investment (ROI) calculation
5. Break-even analysis

Create a cash flow projection over 5 years, considering:
- Initial investment costs
- Monthly rental income
- Ongoing expenses
- Property management fees
- Potential vacancy rates
"""

RISK_ASSESSMENT_PROMPT = """
Identify and analyze potential risks associated with this property investment:
1. Market risks
2. Location-specific risks
3. Financial risks
4. Legal and regulatory risks
5. Maintenance and operational risks

Evaluate the impact of different market scenarios:
- Best case scenario
- Most likely scenario
- Worst case scenario
- Mitigation strategies for each scenario
"""

PROPERTY_EVALUATION_PROMPT = """
Assess the physical condition and potential of the property:
1. Current state of repairs and maintenance
2. Modernization opportunities
3. Energy efficiency rating
4. Potential for value addition

Analyze the property's location advantages and disadvantages:
1. Proximity to amenities
2. Transportation access
3. Neighborhood characteristics
4. Future development plans
"""

INVESTMENT_STRATEGY_PROMPT = """
Develop a comprehensive investment strategy for this property:
1. Short-term vs long-term goals
2. Exit strategy options
3. Capital improvement plans
4. Tenant selection criteria

Compare different investment approaches:
1. Buy-to-hold vs flip
2. Single-family vs multi-family
3. Commercial vs residential
4. Pros and cons of each approach
"""

LEGAL_COMPLIANCE_PROMPT = """
Review the legal considerations for this property investment:
1. Zoning regulations
2. Building codes
3. Landlord-tenant laws
4. Tax implications

Identify any regulatory requirements or restrictions:
1. Building permits needed
2. Environmental regulations
3. Historical preservation requirements
4. Local government approvals
"""

EXIT_STRATEGY_PROMPT = """
Evaluate potential exit strategies for this investment:
1. Sale timing considerations
2. Market conditions for optimal sale
3. Alternative exit options
4. Capital gains implications

Create a contingency plan for unexpected scenarios:
1. Market downturns
2. Property damage
3. Tenant issues
4. Financial challenges
"""

DOCUMENTATION_PROMPT = """
List all required documentation for the investment:
1. Property inspection reports
2. Financial statements
3. Legal agreements
4. Insurance policies
5. Maintenance records

Create a timeline for regular property reviews:
1. Quarterly financial reviews
2. Annual maintenance checks
3. Market condition updates
4. Regulatory compliance checks
"""

SPECIALIZED_ANALYSIS_PROMPT = """
For specialized property types:

Commercial Properties:
1. Tenant mix analysis
2. Lease terms evaluation
3. Commercial zoning benefits
4. Business district impact

Vacation Rentals:
1. Seasonal demand analysis
2. Booking platform requirements
3. Guest management procedures
4. Local tourism trends

Development Opportunities:
1. Feasibility study requirements
2. Construction cost estimates
3. Timeline projections
4. Permitting process overview
"""
