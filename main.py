import sys
from typing import Optional
import asyncio
import click
from pathlib import Path
from agent.agent import Agent,AgentEventType
from ui.tui import TUI,get_console

console = get_console()

class CLI:
    def __init__(self):
        self.agent: Agent | None =  None
        self.tui = TUI(console)

    async def run_single(self, message : str) -> Optional[str]:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)
    
    async def run_interactive(self) -> Optional[str]:
        self.tui.print_welcome(
            'Intializing claude bot',
            lines=[
                f"model: gemini-2.5-flash",
                f"cwd: {Path.cwd()}",
                f"commands: /help /config /approval /model /exit"
            ]
        )
        async with Agent() as agent:
            self.agent = agent
            
            while True:
                try:
                    user_input = console.input("\n[user]>[/user] ").strip()
                    await self._process_message(user_input)
                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit[/dim]")
                except EOFError:
                    break
            
            console.print("\n[dim]Bye from claude[/dim]")

    def _get_tool_kind(self, tool_name : str) -> Optional[str]:
        tool_kind = None
        tool = self.agent.tool_registry.get(tool_name)
        if not tool:
            tool_kind = None
        
        tool_kind = tool.kind.value
        return tool_kind

    async def _process_message(self,message : Optional[str]) -> Optional[str]:
        if not self.agent:
            return None
        
        assistant_streaming = False
        final_response : Optional[str] = None

        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content" , "")
                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming = True
                self.tui.stream_assistant_delta(content)
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error", "Unkown error occured")
                console.print(f"\n[error]Error: {error}[/error]")
            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "unknown") 
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_start(
                    event.data.get("call_id" or ""),
                    tool_name,
                    tool_kind,
                    event.data.get("arguments", {})
                )
            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get("name", "unknown")
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_complete(
                    event.data.get("call_id" or ""),
                    tool_name,
                    tool_kind,
                    event.data.get("success",False),
                    event.data.get("output",""),
                    event.data.get("error"),
                    event.data.get("metadata"),
                    event.data.get("truncated", False),
                )

        return final_response

@click.command()
@click.argument("prompt", required = False)
def main(
    prompt : Optional[str],
):  
    cli = CLI()
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)
    else:
        asyncio.run(cli.run_interactive())

main()