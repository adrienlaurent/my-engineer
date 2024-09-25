from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class LLMResponseContent(BaseModel):
    text: str
    type: str = "text"

class PatchInstruction(BaseModel):
    file_path: str
    patch_content: str
    processed_patch_path: Optional[str] = None

class NewFileInstruction(BaseModel):
    file_path: str
    content: str

class BashScriptInstruction(BaseModel):
    script_name: str
    script_content: str

class LLMResponseMetadata(BaseModel):
    id: str
    model: str
    role: str
    type: str
    usage: Dict[str, int]
    stop_reason: Optional[str] = None
    stop_sequence: Optional[str] = None

class LLMResponse(BaseModel):
    content: List[LLMResponseContent]
    metadata: LLMResponseMetadata
    patches: List[PatchInstruction] = Field(default_factory=list)
    new_files: List[NewFileInstruction] = Field(default_factory=list)
    bash_scripts: List[BashScriptInstruction] = Field(default_factory=list)
    preamble_instructions: Optional[str] = None
    postamble_instructions: Optional[str] = None
    commit_name: Optional[str] = None  
