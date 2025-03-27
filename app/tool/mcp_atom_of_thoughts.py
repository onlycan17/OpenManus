"""MCP Atom of Thoughts tools module."""
from typing import Dict, List, Optional
from app.tool.base import BaseTool

class MCPAtomOfThoughts(BaseTool):
    name: str = "mcp_atom_of_thoughts_AoT"
    description: str = "Atom of Thoughts (AoT) tool for complex problem solving"

    async def execute(self, atomId: str, content: str, atomType: str,
                     dependencies: List[str], confidence: float,
                     depth: Optional[int] = None,
                     isVerified: Optional[bool] = None) -> Dict:
        try:
            result = {
                "atomId": atomId,
                "content": content,
                "atomType": atomType,
                "dependencies": dependencies,
                "confidence": confidence
            }
            if depth is not None:
                result["depth"] = depth
            if isVerified is not None:
                result["isVerified"] = isVerified
            return result
        except Exception as e:
            return {"error": str(e)}

    def to_param(self) -> Dict:
        return {
            "function": {
                "description": self.description,
                "parameters": {
                    "properties": {
                        "atomId": {"type": "string", "description": "Atom identifier"},
                        "content": {"type": "string", "description": "Atom content"},
                        "atomType": {
                            "type": "string",
                            "enum": ["premise", "reasoning", "hypothesis", "verification", "conclusion"]
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["atomId", "content", "atomType", "dependencies", "confidence"]
                }
            }
        }

class MCPAtomOfThoughtsLight(BaseTool):
    name: str = "mcp_atom_of_thoughts_AoT_light"
    description: str = "Lightweight version of Atom of Thoughts (AoT) for faster processing"

    async def execute(self, atomId: str, content: str, atomType: str,
                     dependencies: List[str], confidence: float,
                     depth: Optional[int] = None,
                     isVerified: Optional[bool] = None) -> Dict:
        try:
            result = {
                "atomId": atomId,
                "content": content,
                "atomType": atomType,
                "dependencies": dependencies,
                "confidence": confidence
            }
            if depth is not None:
                result["depth"] = depth
            if isVerified is not None:
                result["isVerified"] = isVerified
            return result
        except Exception as e:
            return {"error": str(e)}

    def to_param(self) -> Dict:
        return {
            "function": {
                "description": self.description,
                "parameters": {
                    "properties": {
                        "atomId": {"type": "string", "description": "Atom identifier"},
                        "content": {"type": "string", "description": "Atom content"},
                        "atomType": {
                            "type": "string",
                            "enum": ["premise", "reasoning", "hypothesis", "verification", "conclusion"]
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["atomId", "content", "atomType", "dependencies", "confidence"]
                }
            }
        }

class MCPAtomOfThoughtsCommands(BaseTool):
    name: str = "mcp_atom_of_thoughts_atomcommands"
    description: str = "Control commands for Atom of Thoughts operations"

    async def execute(self, command: str, atomId: Optional[str] = None,
                     decompositionId: Optional[str] = None,
                     maxDepth: Optional[int] = None) -> Dict:
        try:
            result = {"command": command}
            if atomId:
                result["atomId"] = atomId
            if decompositionId:
                result["decompositionId"] = decompositionId
            if maxDepth:
                result["maxDepth"] = maxDepth
            return result
        except Exception as e:
            return {"error": str(e)}

    def to_param(self) -> Dict:
        return {
            "function": {
                "description": self.description,
                "parameters": {
                    "properties": {
                        "command": {
                            "type": "string",
                            "enum": ["decompose", "complete_decomposition",
                                   "termination_status", "best_conclusion", "set_max_depth"]
                        },
                        "atomId": {"type": "string"},
                        "decompositionId": {"type": "string"},
                        "maxDepth": {"type": "number"}
                    },
                    "required": ["command"]
                }
            }
        }
