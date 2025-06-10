from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.llm.llm_client import LLMClient
from app.tool import (
    Bash,
    BrowserUseTool,
    CreateChatCompletion,
    PlanningTool,
    StrReplaceEditor,
    Terminate,
    ToolCollection,
    WebSearch
)
from app.tool.chart_visualization.python_execute import NormalPythonExecute
from app.tool.chart_visualization.chart_prepare import VisualizationPrepare
from app.tool.chart_visualization.data_visualization import DataVisualization

SYSTEM_PROMPT = """Act as an experienced PE real estate analyst for Danish properties. Review ALL documents in the workspace folder 'Hausers plads30 1. Datarum'. Extract, analyze, and calculate: Property Information (address, type, year, renovation, occupancy, units/sizes),
Financials (rental income, opex, price, gross/net yield with calculation, capex, LTV), and Risks/Opportunities (tenant mix, lease expiries, value-add potential, uncertainties). Produce a single Markdown document named 'Analysis OnePager - Hausers Plads 30.md' in the workspace.
This one-pager must include: 1. Executive Investment Summary (max 1000 words, pros/cons for investment). 2. Key Data & Findings Table (Markdown: Parameter, Value, Source (Filename, page#/cell), Comment/Calculation; include address, type, gross rental income, opex, net yield, key risk, key opportunity,
planned capex, overall recommendation; cite sources precisely; show yield calculation). 3. Further Analysis & Strategic Considerations (3 main uncertainties/red flags; 2-3 specific areas for next DD phase; assess as Core/Core+/Value-add/Opportunistic with justification; recommend further analysis yes/no with reasons).
Output Requirements: Filename 'Analysis OnePager - Hausers Plads 30.md' in workspace, use Markdown, cite sources meticulously, be critical not just descriptive, use professional English, ensure the one-pager is comprehensive and serves as the final analysis conclusion report..
Ask questions if need for clarification or if some info is needed
"""

from app.prompt.toolcall import NEXT_STEP_PROMPT as BASE_NEXT_STEP_PROMPT
NEXT_STEP_PROMPT = BASE_NEXT_STEP_PROMPT


class CustomRealEstateAgent(ToolCallAgent):
    name: str = "Custom_Real_Estate_Analyst"
    description: str = "A custom agent for detailed real estate deal analysis using a comprehensive toolset."

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 15000
    max_steps: int = 50

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Terminate(),
            StrReplaceEditor(),
            WebSearch(),
            Bash(),
            BrowserUseTool(),
            NormalPythonExecute(),
            VisualizationPrepare(),
            DataVisualization(),
            # CreateChatCompletion(), # Uncomment if needed
            # PlanningTool(), # Uncomment if needed
        )
    )

"""    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            system_prompt=self.system_prompt,
            next_step_prompt=self.next_step_prompt,
            use_message_history_summary=True,
            auto_save_message_history=True,
            save_message_history_path=config.workspace_root(),
            model=config.smart_llm_model, # Using smart_llm_model for better analysis
            temperature=0.0,
            available_tools=self.available_tools
        )
"""
