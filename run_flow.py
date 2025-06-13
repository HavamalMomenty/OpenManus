import asyncio
import shutil
import time
import logging
import os
from pathlib import Path

from app.agent.data_analysis import DataAnalysis
from app.agent.manus import Manus
from app.agent.custom_real_estate_agent import CustomRealEstateAgent
from app.config import config
from app.flow.flow_factory import FlowFactory, FlowType
from app.logger import logger


async def run_flow():
    agents = {
        "manus": Manus(),
        "custom_real_estate_analyst": CustomRealEstateAgent()
    }
    if config.run_flow_config.use_data_analysis_agent:
        agents["data_analysis"] = DataAnalysis()
    try:
        # Use predefined query if supplied via config.toml, else ask user.
        prompt = config.run_flow_config.query
        max_steps = config.run_flow_config.max_steps
        logger.info(f"Max steps configured to: {max_steps}")
        if prompt is None:
            prompt = input("Enter your prompt: ")

        if prompt is None or not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        flow = FlowFactory.create_flow(
            flow_type=FlowType.PLANNING,
            agents=agents,
        )
        logger.warning("Processing your request...")

        start_time = time.time()
        result = await asyncio.wait_for(
            flow.execute(prompt),
            timeout=3600,  # 60 minute timeout for the entire execution
        )
        elapsed_time = time.time() - start_time
        logger.info(f"Request processed in {elapsed_time:.2f} seconds")
        logger.info(result)

        # Copy newly generated files to output_dir if configured
        if config.output_dir:
            try:
                run_output_dir = config.run_output_dir
                final_output_dir = config.output_dir / run_output_dir.name

                # Get a set of initial file paths that were copied from the input_dir
                initial_files = set()
                if config.input_dir and config.input_dir.is_dir():
                    for root, _, files in os.walk(config.input_dir):
                        for name in files:
                            relative_path = Path(root).relative_to(config.input_dir) / name
                            initial_files.add(str(relative_path))

                logger.info(f"Copying newly generated files from {run_output_dir} to {final_output_dir}...")
                generated_file_count = 0
                for root, _, files in os.walk(run_output_dir):
                    for name in files:
                        source_path = Path(root) / name
                        relative_path = source_path.relative_to(run_output_dir)

                        # If the file was not part of the initial input, copy it
                        if str(relative_path) not in initial_files:
                            generated_file_count += 1
                            destination_path = final_output_dir / relative_path
                            destination_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_path, destination_path)
                            logger.info(f"  Copied generated file: {relative_path}")

                if generated_file_count > 0:
                    logger.info(f"Output copy successful. Copied {generated_file_count} generated files.")
                else:
                    logger.info("No new files were generated during the run.")
            except Exception as e:
                logger.error(f"Failed to copy outputs to {config.output_dir}: {e}")

    except asyncio.TimeoutError:
        logger.error("Request processing timed out after 1 hour")
        logger.info("Operation terminated due to timeout. Please try a simpler request.")
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # Disconnect from all MCP servers
        # await mcp.disconnect_all()  # This line is commented out because 'mcp' is not defined in the provided code
        logger.info("Disconnected from all MCP servers.")


if __name__ == "__main__":
    asyncio.run(run_flow())
