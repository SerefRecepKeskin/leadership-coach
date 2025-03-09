from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.schema import QueryBundle
from llama_index.core.response import Response
from pydantic import BaseModel
import requests
import logging

class WebSearchTool(BaseToolSpec):
    spec_functions = ["search"]
    
    def search(self, query: str) -> str:
        try:
            response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&kl=tr-tr")
            response.raise_for_status()  # Raise an HTTPError for bad responses
            data = response.json()
            abstract = data.get("Abstract", "")
            url = data.get("AbstractURL", "")
            return f"{abstract}\nSource: {url}" if abstract else "No relevant info found."
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP request failed: {str(e)}")
            return f"Web search failed: {str(e)}"
        except ValueError as e:
            logging.error(f"JSON decoding failed: {str(e)}")
            return f"Web search failed: {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return f"Web search failed: {str(e)}"
    
    def to_query_engine(self):
        """Convert the tool to a query engine."""
        class WebSearchQueryEngine(CustomQueryEngine, BaseModel):
            search_fn: callable

            def custom_query(self, query_bundle: QueryBundle) -> Response:
                search_result = self.search_fn(query_bundle.query_str)
                return Response(response=search_result)
        
        return WebSearchQueryEngine(search_fn=self.search)