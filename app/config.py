import json
import threading
import tomllib
import shutil
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
# -----------------------------------------------------
# Workspace directory
# -----------------------------------------------------
# WORKSPACE_ROOT will be defined in the Config class and loaded from config.toml


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="Azure, Openai, or Ollama")
    api_version: str = Field(..., description="Azure Openai version if AzureOpenai")


### ADDED BY BJARKE
class ManusAgentSettings(BaseModel):
    """Configuration specific to the Manus agent"""
    max_steps: int = Field(default=10, description="Maximum steps for Manus agent execution")

class RealEstateAgentSettings(BaseModel):
    """Configuration specific to the Real Estate agent"""
    max_steps: int = Field(default=20, description="Maximum steps for Real Estate agent execution")


class ProxySettings(BaseModel):
    server: str = Field(None, description="Proxy server address")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")


class SearchSettings(BaseModel):
    engine: str = Field(default="Google", description="Search engine the llm to use")
    fallback_engines: List[str] = Field(
        default_factory=lambda: ["DuckDuckGo", "Baidu", "Bing"],
        description="Fallback search engines to try if the primary engine fails",
    )
    retry_delay: int = Field(
        default=60,
        description="Seconds to wait before retrying all engines again after they all fail",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of times to retry all engines when all fail",
    )
    lang: str = Field(
        default="en",
        description="Language code for search results (e.g., en, zh, fr)",
    )
    country: str = Field(
        default="dk",
        description="Country code for search results (e.g., dk, cn, uk, us)",
    )


class RunflowSettings(BaseModel):
    use_data_analysis_agent: bool = Field(
        default=False, description="Enable data analysis agent in run flow"
    )
    bfe_number: Optional[int] = Field(
        default=None, description="BFE number for the run"
    )
    query: Optional[str] = Field(
        default=None, description="Optional default prompt to execute instead of interactive input"
    )
    max_steps: int = Field(
        default=5, description="Maximum number of steps for the agent to execute"
    )


class BrowserSettings(BaseModel):
    headless: bool = Field(True, description="Whether to run browser in headless mode")
    disable_security: bool = Field(
        True, description="Disable browser security features"
    )
    extra_chromium_args: List[str] = Field(
        default_factory=list, description="Extra arguments to pass to the browser"
    )
    chrome_instance_path: Optional[str] = Field(
        None, description="Path to a Chrome instance to use"
    )
    wss_url: Optional[str] = Field(
        None, description="Connect to a browser instance via WebSocket"
    )
    cdp_url: Optional[str] = Field(
        None, description="Connect to a browser instance via CDP"
    )
    proxy: Optional[ProxySettings] = Field(
        None, description="Proxy settings for the browser"
    )
    max_content_length: int = Field(
        2000, description="Maximum length for content retrieval operations"
    )


class SandboxSettings(BaseModel):
    """Configuration for the execution sandbox"""

    use_sandbox: bool = Field(False, description="Whether to use the sandbox")
    image: str = Field("python:3.12-slim", description="Base image")
    work_dir: str = Field("/workspace", description="Container working directory")
    memory_limit: str = Field("512m", description="Memory limit")
    cpu_limit: float = Field(1.0, description="CPU limit")
    timeout: int = Field(300, description="Default command timeout (seconds)")
    network_enabled: bool = Field(
        False, description="Whether network access is allowed"
    )


class ResightsSettings(BaseModel):
    """Configuration for the Resights API"""
    base_url: Optional[str] = Field("https://api.resights.dk/api/v2", description="Resights API base URL")
    api_key: Optional[str] = Field(None, description="Resights API key")


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server"""

    type: str = Field(..., description="Server connection type (sse or stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(
        default_factory=list, description="Arguments for stdio command"
    )


class MCPSettings(BaseModel):
    """Configuration for MCP (Model Context Protocol)"""

    server_reference: str = Field(
        "app.mcp.server", description="Module reference for the MCP server"
    )
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )

    @classmethod
    def load_server_config(cls) -> Dict[str, MCPServerConfig]:
        """Load MCP server configuration from JSON file"""
        config_path = PROJECT_ROOT / "config" / "mcp.json"

        try:
            config_file = config_path if config_path.exists() else None
            if not config_file:
                return {}

            with config_file.open() as f:
                data = json.load(f)
                servers = {}

                for server_id, server_config in data.get("mcpServers", {}).items():
                    servers[server_id] = MCPServerConfig(
                        type=server_config["type"],
                        url=server_config.get("url"),
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                    )
                return servers
        except Exception as e:
            raise ValueError(f"Failed to load MCP server config: {e}")


# -----------------------------------------------------
# I/O DIRECTORY SETTINGS
# -----------------------------------------------------
# IOSettings class removed, workspace_root will be used instead.


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]
    workspace_root: Path = Field(..., description="Root directory for all application data, inputs, and outputs")
    input_dir: Optional[Path] = Field(None, description="Optional directory from which to copy initial files to workspace_root")
    output_dir: Optional[Path] = Field(None, description="Optional directory to copy run outputs to after completion")
    sandbox: Optional[SandboxSettings] = Field(
        None, description="Sandbox configuration"
    )
    browser_config: Optional[BrowserSettings] = Field(
        None, description="Browser configuration"
    )
    search_config: Optional[SearchSettings] = Field(
        None, description="Search configuration"
    )
    mcp_config: Optional[MCPSettings] = Field(None, description="MCP configuration")
    run_flow_config: Optional[RunflowSettings] = Field(
        None, description="Run flow configuration"
    )
    resights_config: ResightsSettings = Field(default_factory=ResightsSettings)
    # io_config removed

    #Added by bjarke:     We set the parameters of the manus and real estate agents. 
    manus_agent_config: ManusAgentSettings = Field(
        default_factory=ManusAgentSettings,
        description="Manus agent specific configuration"
    )
    real_estate_agent_config: RealEstateAgentSettings = Field(
        default_factory=RealEstateAgentSettings,
        description="Real Estate agent specific configuration"
    )

    class Config:
        arbitrary_types_allowed = True


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    print("[Config] Initializing configuration...")
                    self._load_initial_config()

                    # The original workspace_root from config.toml
                    base_workspace_root = self.workspace_root
                    print(f"[Config] Base workspace root is: {base_workspace_root}")

                    # Create a timestamped subdirectory for this run's outputs
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    runs_base_dir = base_workspace_root / "runs"
                    self._run_output_dir = runs_base_dir / ts
                    self._run_output_dir.mkdir(parents=True, exist_ok=True)
                    print(f"[Config] Created run-specific workspace: {self._run_output_dir}")

                    # IMPORTANT: Re-assign workspace_root to be the run-specific directory for this run
                    self._config.workspace_root = self._run_output_dir
                    print(f"[Config] Active workspace for this run is now: {self.workspace_root}")

                    # If an input directory is specified, copy its contents into the new run-specific workspace
                    print(f"[Config] Checking for input_dir. Value: {self.input_dir}")
                    if self.input_dir:
                        print(f"[Config] Recursively copying all contents from '{self.input_dir}' to '{self.workspace_root}'...")
                        if not self.input_dir.is_dir():
                            print(f"[Config] ERROR: Input directory '{self.input_dir}' is not a valid directory. Skipping copy.")
                            return

                        try:
                            # This recursively copies everything from the input_dir into the new run-specific workspace.
                            shutil.copytree(str(self.input_dir), str(self.workspace_root), dirs_exist_ok=True)
                            print("[Config] Recursive file copy process completed successfully.")
                        except Exception as e:
                            print(f"[Config] ERROR: An error occurred during recursive file copy: {e}")
                    else:
                        print("[Config] No input_dir configured. Skipping file copy.")

                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "max_input_tokens": base_llm.get("max_input_tokens"),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
        }

        # handle browser config.
        browser_config = raw_config.get("browser", {})
        browser_settings = None

        if browser_config:
            # handle proxy settings.
            proxy_config = browser_config.get("proxy", {})
            proxy_settings = None

            if proxy_config and proxy_config.get("server"):
                proxy_settings = ProxySettings(
                    **{
                        k: v
                        for k, v in proxy_config.items()
                        if k in ["server", "username", "password"] and v
                    }
                )

            # filter valid browser config parameters.
            valid_browser_params = {
                k: v
                for k, v in browser_config.items()
                if k in BrowserSettings.__annotations__ and v is not None
            }

            # if there is proxy settings, add it to the parameters.
            if proxy_settings:
                valid_browser_params["proxy"] = proxy_settings

            # only create BrowserSettings when there are valid parameters.
            if valid_browser_params:
                browser_settings = BrowserSettings(**valid_browser_params)

        search_config = raw_config.get("search", {})
        search_settings = None
        if search_config:
            search_settings = SearchSettings(**search_config)
        sandbox_config = raw_config.get("sandbox", {})
        if sandbox_config:
            sandbox_settings = SandboxSettings(**sandbox_config)
        else:
            sandbox_settings = SandboxSettings()

        mcp_config = raw_config.get("mcp", {})
        mcp_settings = None
        if mcp_config:
            # Load server configurations from JSON
            mcp_config["servers"] = MCPSettings.load_server_config()
            mcp_settings = MCPSettings(**mcp_config)
        else:
            mcp_settings = MCPSettings(servers=MCPSettings.load_server_config())

        run_flow_config = raw_config.get("runflow")
        if run_flow_config:
            run_flow_settings = RunflowSettings(**run_flow_config)
        else:
            run_flow_settings = RunflowSettings()

        resights_config = raw_config.get("resights")
        if resights_config:
            resights_settings = ResightsSettings(**resights_config)
        else:
            resights_settings = ResightsSettings()

        # ---------------- I/O Config from [io] table ----------------
        io_config_raw = raw_config.get("io", {})

        # --- Workspace Root Config (Required) ---
        workspace_root_str = io_config_raw.get("workspace_root")
        if not workspace_root_str:
            raise ValueError(
                "'workspace_root' must be defined under the [io] table in config.toml. "
                'Example: [io]\nworkspace_root = "path/to/workspace"'
            )
        workspace_path = Path(str(workspace_root_str)).expanduser().resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)

        # --- Input Directory Config (Optional) ---
        input_dir_str = io_config_raw.get("input_dir")
        input_path = None
        if input_dir_str:
            input_path = Path(str(input_dir_str)).expanduser().resolve()
            if not input_path.exists():
                print(f"[Config] WARNING: input_dir '{input_path}' did not exist. Creating it now. It is empty.")
                input_path.mkdir(parents=True, exist_ok=True)
            elif not input_path.is_dir():
                raise ValueError(f"Configured input_dir '{input_path}' under [io] is not a directory.")

        # --- Output Directory Config (Optional) ---
        output_dir_str = io_config_raw.get("output_dir")
        output_path = None
        if output_dir_str:
            output_path = Path(str(output_dir_str)).expanduser().resolve()
            output_path.mkdir(parents=True, exist_ok=True)

        # breakpoint() was here, removed.
        config_dict = {
            "llm": {
                "default": default_settings,
                **{
                    name: {**default_settings, **override_config}
                    for name, override_config in llm_overrides.items()
                },
            },
            "workspace_root": workspace_path,
            "input_dir": input_path, # Added optional input_dir
            "output_dir": output_path, # Added optional output_dir
            "sandbox": sandbox_settings,
            "browser_config": browser_settings,
            "search_config": search_settings,
            "mcp_config": mcp_settings,
            "run_flow_config": run_flow_settings,
            "resights_config": resights_settings,
            # "io_config" removed
        }

        #Added by bjarke:     We set the parameters of the manus and real estate agents. 
        config_dict.update(
            manus_agent_config=ManusAgentSettings(**raw_config.get("manus_agent", {})),
            real_estate_agent_config=RealEstateAgentSettings(
                **raw_config.get("real_estate_agent", {})
            ),
        )

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def sandbox(self) -> SandboxSettings:
        return self._config.sandbox

    @property
    def browser_config(self) -> Optional[BrowserSettings]:
        return self._config.browser_config

    @property
    def search_config(self) -> Optional[SearchSettings]:
        return self._config.search_config

    @property
    def mcp_config(self) -> MCPSettings:
        """Get the MCP configuration"""
        return self._config.mcp_config

    @property
    def run_flow_config(self) -> RunflowSettings:
        """Get the Run Flow configuration"""
        return self._config.run_flow_config

    @property
    def resights_config(self) -> ResightsSettings:
        """Get the Resights API configuration"""
        return self._config.resights_config

    @property
    def workspace_root(self) -> Path:
        # This property now returns the main workspace_root from AppConfig
        return self._config.workspace_root

    @property
    def input_dir(self) -> Optional[Path]:
        return self._config.input_dir

    @property
    def output_dir(self) -> Optional[Path]:
        return self._config.output_dir

    # The run_output_dir property still provides the path to the current run's output directory.

    # Directory for this particular execution run
    @property
    def run_output_dir(self) -> Path:
        return self._run_output_dir

    @property
    def manus_agent_config(self) -> ManusAgentSettings:
        return self._config.manus_agent_config

    @property
    def real_estate_agent_config(self) -> RealEstateAgentSettings:
        return self._config.real_estate_agent_config

config = Config()
