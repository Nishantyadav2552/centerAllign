from typing import Dict, Any, Optional
from backend.app.tools.registry import tool_registry

@tool_registry.register(
    name="browser_open",
    description="Open an allowed page in the controlled demo environment.",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Allowed URL to open (e.g. /portal or http://127.0.0.1:8000/portal)"}
        },
        "required": ["url"]
    },
    permission="read"
)
def browser_open(context: Dict[str, Any], url: str) -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.open(url)

@tool_registry.register(
    name="browser_search",
    description="Search the vendor portal using an accessible search query.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Vendor name, invoice number, or search terms"},
            "scenario": {"type": "string", "description": "Optional scenario flag, e.g. recoverable_failure"}
        },
        "required": ["query"]
    },
    permission="read"
)
def browser_search(context: Dict[str, Any], query: str, scenario: Optional[str] = None) -> Dict[str, Any]:
    browser = context["browser_service"]
    active_scenario = scenario or context.get("scenario")
    return browser.search(query, scenario=active_scenario)

@tool_registry.register(
    name="browser_extract_page",
    description="Extract relevant structured information and invoice rows from the current page.",
    input_schema={"type": "object", "properties": {}},
    permission="read"
)
def browser_extract_page(context: Dict[str, Any]) -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.extract_page()

@tool_registry.register(
    name="browser_click",
    description="Click a validated target identifier or link in the current page.",
    input_schema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Selector, button id, or link keyword to click"}
        },
        "required": ["target"]
    },
    permission="read"
)
def browser_click(context: Dict[str, Any], target: str) -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.click(target)

@tool_registry.register(
    name="browser_fill",
    description="Fill a validated form field with text.",
    input_schema={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "Form input selector or field identifier"},
            "value": {"type": "string", "description": "Text value to fill"}
        },
        "required": ["selector", "value"]
    },
    permission="read"
)
def browser_fill(context: Dict[str, Any], selector: str, value: str) -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.fill(selector, value)

@tool_registry.register(
    name="browser_download",
    description="Download a permitted invoice PDF and return its local artifact reference.",
    input_schema={
        "type": "object",
        "properties": {
            "download_url": {"type": "string", "description": "Relative or full URL to download"}
        },
        "required": ["download_url"]
    },
    permission="read"
)
def browser_download(context: Dict[str, Any], download_url: str) -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.download(download_url)

@tool_registry.register(
    name="browser_screenshot",
    description="Capture a screenshot for debugging and visual audit evidence.",
    input_schema={
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "Descriptive tag for the screenshot"}
        }
    },
    permission="read"
)
def browser_screenshot(context: Dict[str, Any], label: str = "audit") -> Dict[str, Any]:
    browser = context["browser_service"]
    return browser.screenshot(label)
