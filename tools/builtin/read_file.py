from pydantic import BaseModel,Field
from tools.base import Tool,ToolKind,ToolInvocation,ToolResult
from utils.paths import resolve_path,is_binary_file
from utils.text import count_token,truncate_text
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()
model = os.getenv('MODEL')

class ReadFileParams(BaseModel):
    path : str = Field(
        ..., 
        description = "Path of the file to read (relative to the working directory or absolute path)"
    )

    offset : int = Field(
        1,
        ge = 1,
        description = "Line number to start reading from (1 based)"
    )

    limit : Optional[int] = Field(
        None,
        ge = 1,
        description = "Maximum number of lines to read. If not given read entire file"
    )

class ReadFileTool(Tool):
    name = "read_file"

    description = (
        "Read and retrieve the contents of a text-based file from the filesystem. "
        "This tool displays file content with line numbers prepended to each line for easy reference. "
        
        "SUPPORTED FILE TYPES:\n"
        "- Text files: .txt, .md, .csv, .tsv, .log\n"
        "- Code files: .py, .js, .java, .cpp, .c, .h, .css, .html, .xml, .json, .yaml, .yml\n"
        "- Configuration files: .conf, .cfg, .ini, .env\n"
        "- Documentation: .rst, .tex\n"
        "- Any UTF-8 encoded text file\n"
        
        "PARAMETERS:\n"
        "- filepath (required): Absolute or relative path to the file to read\n"
        "- offset (optional): Starting line number (0-indexed). Use for large files to skip initial lines. Default: 0\n"
        "- limit (optional): Maximum number of lines to read from offset. Use to read files in chunks. Default: read entire file\n"
        
        "OUTPUT FORMAT:\n"
        "Returns content with line numbers in format: '<line_number>: <content>'\n"
        "Example:\n"
        "1: import os\n"
        "2: import sys\n"
        "3: \n"
        "4: def main():\n"
        
        "USAGE EXAMPLES:\n"
        "- Read entire file: read_file('/path/to/script.py')\n"
        "- Read lines 100-200: read_file('/path/to/large.log', offset=100, limit=100)\n"
        "- Read first 50 lines: read_file('/path/to/data.csv', limit=50)\n"
        
        "LIMITATIONS:\n"
        "- Cannot read binary files (executables, images, videos, PDFs, compiled files)\n"
        "- Cannot read files requiring special permissions without proper access\n"
        "- For extremely large files (>10MB), consider using offset/limit to avoid memory issues\n"
        "- Will fail on non-UTF-8 encoded files unless they're ASCII compatible\n"
        
        "ERROR HANDLING:\n"
        "- Returns error if file doesn't exist\n"
        "- Returns error if insufficient permissions\n"
        "- Returns error if file is binary/non-text\n"
        "- Returns error if offset exceeds file length\n"
        
        "BEST PRACTICES:\n"
        "- Always verify file path exists before reading\n"
        "- Use offset/limit for files larger than a few thousand lines\n"
        "- Check file extension to ensure it's a text format before attempting to read\n"
        "- For multi-gigabyte log files, read in chunks using offset/limit to avoid timeouts"
    )
    
    kind = ToolKind.READ

    schema = ReadFileParams

    MAX_FILE_SIZE = 1024*1024*10
    MAX_FILE_TOKENS = 30000

    async def execute(self, invocation : ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(f"Path not found: {path}")
        
        if not path.is_file():
            return ToolResult.error_result(f"Path is not a file: {path}")

        file_size = path.stat().st_size

        if file_size > self.MAX_FILE_SIZE:
            return ToolResult.error_result(
                f"File too large ({file_size / (1024*1024):.1f}MB). "
                f"Maximum is {self.MAX_FILE_SIZE / (1024*1024):.0f}MB."
            )
        
        if is_binary_file(path):
            file_size_mb = file_size / (1024 * 1024)
            size_str = (
                f"{file_size_mb:.2f}MB" if file_size_mb >= 1 else f"{file_size} bytes"
            )
            return ToolResult.error_result(
                f"Cannot read binary file: {path.name} ({size_str}) "
                f"This tool only reads text files."
            )
        
        try:
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = path.read_text(encoding='latin-1')

            lines = content.splitlines()
            total_lines = len(lines)

            if total_lines == 0:
                return ToolResult.success_result(
                    "File is empty nothing to read.",
                    metadata = {
                        "lines" : 0,
                    }
                )
            
            start_idx = max(0,params.offset - 1)

            if params.limit is not None:
                end_idx = min(start_idx + params.limit,total_lines)
            else:
                end_idx = total_lines
            
            selected_lines = lines[start_idx : end_idx]

            formatted_lines = []

            for i, line in enumerate(selected_lines, start=start_idx + 1):
                formatted_lines.append(f"{i:6}|{line}")

            output = "\n".join(formatted_lines)
            token_count = count_token(output,model)
            truncated = False

            if token_count > self.MAX_FILE_TOKENS:
                output = truncate_text(
                    output,
                    self.MAX_FILE_TOKENS,
                    suffix = f"Truncated {total_lines} total lines"
                ) 
                truncated = True
            
            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"Showing lines {start_idx+1}-{end_idx} of {total_lines}"
                )

            if metadata_lines:
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output
            
            return ToolResult.success_result(
                output=output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "shown_start": start_idx + 1,
                    "shown_end": end_idx,
                },
            )
    
        except Exception as e:
            return ToolResult.error_result(f"Failed to read file: {e}")




