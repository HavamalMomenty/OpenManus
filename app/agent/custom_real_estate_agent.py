from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.tool.ask_human import AskHuman
from app.tool import (
    Bash,
    BrowserUseTool,
    CreateChatCompletion,
    PlanningTool,
    StrReplaceEditor,
    Terminate,
    ToolCollection,
    WebSearch,
)
from app.tool.chart_visualization.python_execute import NormalPythonExecute
from app.tool.chart_visualization.chart_prepare import VisualizationPrepare
from app.tool.chart_visualization.data_visualization import DataVisualization
from app.tool.resight_api import FetchResightPropertyTableTool

SYSTEM_PROMPT = """
# Mission
You are a world-class private equity real estate analyst specializing in the Danish property market. Your mission is to conduct a thorough investment analysis of a target property based on the documents provided in the workspace and data from external tools.

# Context
You will be given a BFE number and a set of documents (e.g., information memorandums, rent rolls, financial statements) for a specific property. Your analysis must be critical, meticulous, and backed by evidence from the provided sources.

To access pdf data use this example call pdftotext on /"realestatename"_IM.pdf 
You will be checking the resights API for extra information, and make a SIMILAR document with everything that is in the IC Example.md
# Guiding Principles
-   **Be Critical**: Do not simply regurgitate information. Analyze it.
-   **Cite Everything**: Every piece of data must have a source.
-   **No Synthetic Data**: Never invent or assume data. If information is missing, state it and explain its potential impact.
-   **Professional Language**: Use clear, concise, and professional English.
-   **Ask for Help**: If you are unsure about something or need clarification, ask questions.
"""

from app.prompt.toolcall import NEXT_STEP_PROMPT as BASE_NEXT_STEP_PROMPT
NEXT_STEP_PROMPT = BASE_NEXT_STEP_PROMPT


class CustomRealEstateAgent(ToolCallAgent):
    name: str = "Custom_Real_Estate_Analyst"
    description: str = "A custom agent for detailed real estate deal analysis using a comprehensive toolset. Looking at data in Resights and the investments memorandum given"

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 15000
    max_steps: int = config.real_estate_agent_config.max_steps  # Use config value


    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            Terminate(),
            StrReplaceEditor(),
            #WebSearch(),
            #Bash(),
            BrowserUseTool(),
            NormalPythonExecute(),
            #VisualizationPrepare(),
            #DataVisualization(),
            FetchResightPropertyTableTool(
                api_key=config.resights_config.api_key
            ),
            #AskHuman(),
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
