from pathlib import Path
from typing import List
import logging
from runloop_api_client import Runloop
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DevboxManager:
    def __init__(self, devbox_id: str, runloop_api_key: str):
        self.devbox_id = devbox_id
        self.runloop_api_key = runloop_api_key
        self.runloop_client: Runloop | None = None
        self.init_devbox(devbox_id)
        
    def init_devbox(self, devbox_id: str):
        """Initialize the devbox client and check its existence."""
        self.runloop_client = self.get_runloop_client()
        res = self.check_devbox_exists(devbox_id)
        logger.info(f"Devbox exists: {devbox_id} | {res.status}")
        if not res:
            logger.info(f"Devbox does not exist: {devbox_id}")
            self.create_devbox()
        elif res and res.status == "suspended":
            logger.info(f"Devbox exists and is suspended: {devbox_id}")
            self.resume_devbox(devbox_id)
        elif res and res.status == "shutdown":
            logger.info(f"Devbox exists and is stutdown: {devbox_id}")
            devbox = self.create_devbox()
            logger.info(f"Devbox created: {devbox}")
        else:
            logger.info(f"Devbox exists and is running: {devbox_id}")
        
    def get_runloop_client(self):
        """Create and return a Runloop client instance."""
        if self.runloop_client is None:
            if not self.runloop_api_key:
                logger.error(f"Environment variable {self.runloop_api_key} not set.")
                raise ValueError(f"Environment variable {self.runloop_api_key} not set.")
            self.runloop_client = Runloop(bearer_token=self.runloop_api_key)
        return self.runloop_client

    def check_devbox_exists(self, devbox_id: str):
        """Check if a Devbox with the given ID exists on Runloop.ai."""
        try:
            devbox = self.runloop_client.devboxes.retrieve(devbox_id)
            return devbox
        except Exception as e:
            logger.error(f"Failed to get Devbox: {e}")
            raise

    def create_devbox(self):
        """Create a Devbox on Runloop.ai and return its ID."""
        devbox_name = "Chinook-Devbox"
        
        try:
            devbox = self.runloop_client.devboxes.create_and_await_running(
                name=devbox_name,
                blueprint_id="bpt_2yvlYIf2ktWWRZKFvN9Z8",
                # setup_commands=[
                #     "sudo apt-get update",
                #     "sudo apt-get install -y python3-pip",
                #     "pip3 install pandas matplotlib",
                #     "pip3 install openai",
                #     "pip3 install runloop-api-client",
                #     "pip3 install mcp",
                #     "pip3 install python-dotenv",
                #     "pip3 install sqlite3"
                # ],
                launch_parameters={
                    "after_idle": {
                        "idle_time_seconds": 1800,
                        "on_idle": "suspend"
                    },
                }
            )
            logger.info(f"Devbox created: {devbox.id}")
            self.devbox_id = str(devbox.id)
            os.environ["DEVBOX_ID"] = str(devbox.id)
            return devbox.id
        except Exception as e:
            logger.error(f"Failed to create Devbox: {e}")
            raise
    
    async def resume_devbox(self, devbox_id: str):
        """Resume a suspended Devbox on Runloop.ai."""
        try:
            devbox = await self.runloop_client.devboxes.await_running(devbox_id)
            logger.info(f"Devbox resumed: {devbox.id}")
            return devbox
        except Exception as e:
            logger.error(f"Failed to resume Devbox: {e}")
            raise        
    
    def ensure_mcp_files(self, local_dir: Path) -> bool:
        """
        Ensures MCP files are present in devbox
        Returns True if files were uploaded, False if they were already present
        """
        required_files = {
            "Chinook_Sqlite.sqlite": "/home/user/Chinook_Sqlite.sqlite",
            "client.py": "/home/user/client.py",
            "server.py": "/home/user/server.py",
            ".env": "/home/user/.env"
        }
        
        files_uploaded = False
        
        try:
            for local_file, remote_path in required_files.items():
                local_file_path = local_dir / local_file
                if not local_file_path.exists():
                    logger.error(f"Local file {local_file} not found in {local_dir}")
                    raise FileNotFoundError(f"Required file {local_file} not found")
                
                try:
                    with open(local_file_path, "rb") as file:
                        self.runloop_client.devboxes.upload_file(
                            self.devbox_id,
                            path=remote_path,
                            file=file
                        )
                    logger.info(f"File {local_file} uploaded successfully")
                    files_uploaded = True
                except Exception as e:
                    logger.error(f"Failed to upload {local_file}: {e}")
                    raise
                    
            return files_uploaded
            
        except Exception as e:
            logger.error(f"Error ensuring MCP files: {e}")
            raise
    
    async def run_mcp_query(self, query: str) -> dict:
        """
        Execute a natural language query using the MCP server on the devbox
        
        Args:
            query: Natural language query to execute
            
        Returns:
            Dict containing query results
        """
        try:
            # The command to run client.py with the query
            cmd = f"cd /home/user && python client.py Chinook_Sqlite.sqlite '{query}'"
            
            old_result = self.runloop_client.devboxes.execute_sync(self.devbox_id, command="ls", shell_name="my-shell")
            logger.info(old_result.stdout)
            
            # Execute the command in a shell that can receive input
            result = self.runloop_client.devboxes.execute_sync(
                self.devbox_id,
                command=cmd,
                shell_name="mcp-shell"  # Use a named shell for interaction
            )
            
            logger.info(f"Result generated successfully\n {result.stdout}")
            output = result.stdout
            
            logger.info(f"Output Error: {result.stderr}") 
            
            # Extract JSON array from output
            try:
                # Look for array pattern in the output
                array_start = output.find('[')
                array_end = output.rfind(']') + 1
                if array_start >= 0 and array_end > array_start:
                    json_str = output[array_start:array_end]
                    data = json.loads(json_str)
                else:
                    # If no JSON array found, return raw output
                    data = {"raw_output": output}
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw output
                data = {"raw_output": output}
            
            return data
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    async def run_visualization_code(self, code: str) -> str:
        """
        Execute visualization code on the devbox and return the JSON output.
        
        Args:
            code: Visualization code to execute on the devbox
        """
        try:
            self.runloop_client.devboxes.write_file_contents(
                self.devbox_id,
                file_path="/home/user/visualization.py",
                contents=code
            )
            
            # The command to run the visualization code
            cmd = f"cd /home/user && python visualization.py"
            
            # Execute the command in a shell that can receive input
            result = self.runloop_client.devboxes.execute_sync(
                self.devbox_id,
                command=cmd,
                shell_name="viz-shell"  # Use a named shell for visualization
            )
            
            logger.info(f"Visualization code executed successfully\n {result.stdout}")
            
            if result.stderr:
                logger.error(f"Error executing visualization code: {result.stderr}")
                raise RuntimeError(f"Error executing visualization code: {result.stderr}")
            
            return result.stdout
        except Exception as e:
            logger.error(f"Error executing visualization code: {e}")
            raise