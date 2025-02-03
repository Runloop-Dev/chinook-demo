import sys
import os
from dotenv import load_dotenv
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
import logging
import openai

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENAI_API_KEY_ENV = "OPENAI_API"

def generate_sql_query(prompt: str, schema_info: str) -> str:
    """
    Generate SQL query using OpenAI API based on natural language prompt and schema information.
    
    Args:
        prompt (str): Natural language query prompt
        schema_info (str): Database schema information to provide context
        
    Returns:
        str: Generated SQL query
    """
    try:
        system_prompt = f"""
        You are an SQL expert. Generate a SQL query based on the user's request.
        Use the following schema information to create an accurate query:
        {schema_info}
        
        Return ONLY the SQL query, nothing else.
        """
        
        openai.api_key = os.getenv(OPENAI_API_KEY_ENV)
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Lower temperature for more focused SQL generation
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate query: {e}")
        raise

async def interact_with_mcp_server(db_path: str, user_query: str):
    """
    Interacts with the SQLite MCP server to perform a single database operation using natural language query.
    
    Args:
        db_path (str): Path to the SQLite database file.
        user_query (str): Natural language query from user.
    """
    server_params = StdioServerParameters(
        command="python",
        args=["server.py", db_path],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Get schema information for context
                tables_result = await session.call_tool("list_tables")
                tables = eval(tables_result.content[0].text)
                
                # Build schema information for OpenAI
                schema_info = []
                for table in tables:
                    table_name = table['name']
                    schema_result = await session.call_tool(
                        "describe_table", 
                        arguments={"table_name": table_name}
                    )
                    schema_info.append(f"Table {table_name}:")
                    schema_info.append(schema_result.content[0].text)
                
                schema_context = "\n".join(schema_info)
                
                try:
                    # Generate SQL query using OpenAI
                    sql_query = generate_sql_query(user_query, schema_context)
                    print(f"Generated SQL Query:\n{sql_query}\n")
                        
                    # Execute the generated query
                    result = await session.call_tool(
                        "read_query",
                        arguments={"query": sql_query}
                    )
                        
                    # Print results and exit
                    print(result.content[0].text)
                        
                    # Add insight before exiting
                    insight = f"Query executed: {user_query}"
                    await session.call_tool(
                        "append_insight",
                        arguments={"insight": insight}
                    )

                except Exception as e:
                    print(f"Error: {str(e)}", file=sys.stderr)
                    sys.exit(1)

    except Exception as e:
        print(f"Error during server interaction: {e}", file=sys.stderr)
        sys.exit(1)
    except asyncio.CancelledError:
        print("Operation was canceled", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python client.py <db_path> <query>", file=sys.stderr)
        sys.exit(1)

    db_path = sys.argv[1]  # Get the database path from command-line arguments
    user_query = sys.argv[2]  # Get the query from command-line arguments
    
    import asyncio
    asyncio.run(interact_with_mcp_server(db_path, user_query))